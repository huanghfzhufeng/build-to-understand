"""Lifecycle tests: each pins one property of the reconciliation loop.

A controllable Clock stands in for wall-clock time so "idle for 30 days" is a
deterministic step, not a sleep.
"""

import pytest

from mini_object_store import Action, Catalog, Lifecycle, Rule, Store, Tier

BUCKET = "media"


class Clock:
    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


@pytest.fixture
def cat(tmp_path):
    clock = Clock()
    catalog = Catalog(Store(tmp_path / "hot"), Store(tmp_path / "cold"), clock=clock)
    return catalog, clock


def test_put_lands_hot(cat):
    catalog, _ = cat
    catalog.put(BUCKET, "videos/a.mp4", b"data")
    assert catalog.info(BUCKET, "videos/a.mp4").tier is Tier.HOT
    assert catalog.get(BUCKET, "videos/a.mp4") == b"data"


def test_idle_object_moves_to_cold_and_bytes_physically_relocate(cat):
    catalog, clock = cat
    catalog.put(BUCKET, "videos/a.mp4", b"cold-me")
    life = Lifecycle(catalog, [Rule("videos/", Action.TRANSITION_COLD, older_than=30)])

    clock.advance(31)
    report = life.run()

    assert report == [("videos/a.mp4", "-> cold")]
    info = catalog.info(BUCKET, "videos/a.mp4")
    assert info.tier is Tier.COLD
    # The bytes really moved: gone from hot, present in cold.
    assert catalog.hot.get(BUCKET, "videos/a.mp4") is None
    assert catalog.cold.get(BUCKET, "videos/a.mp4") == b"cold-me"
    # And a read still finds them via the catalog.
    assert catalog.get(BUCKET, "videos/a.mp4") == b"cold-me"


def test_a_read_resets_the_idle_clock_and_keeps_it_hot(cat):
    catalog, clock = cat
    catalog.put(BUCKET, "videos/a.mp4", b"warm")
    life = Lifecycle(catalog, [Rule("videos/", Action.TRANSITION_COLD, older_than=30)])

    clock.advance(20)
    catalog.get(BUCKET, "videos/a.mp4")  # touched at t+20
    clock.advance(20)  # 40 since put, but only 20 since the touch
    report = life.run()

    assert report == []  # still hot: idle < 30
    assert catalog.info(BUCKET, "videos/a.mp4").tier is Tier.HOT


def test_expiry_deletes_the_object_entirely(cat):
    catalog, clock = cat
    catalog.put(BUCKET, "tmp/scratch", b"junk")
    life = Lifecycle(catalog, [Rule("tmp/", Action.EXPIRE, older_than=10)])

    clock.advance(11)
    report = life.run()

    assert report == [("tmp/scratch", "expired")]
    assert catalog.info(BUCKET, "tmp/scratch") is None
    assert catalog.get(BUCKET, "tmp/scratch") is None
    assert catalog.hot.get(BUCKET, "tmp/scratch") is None


def test_object_walks_hot_then_cold_then_expired_across_runs(cat):
    catalog, clock = cat
    catalog.put(BUCKET, "videos/a.mp4", b"lifecycle")
    # Expire listed FIRST so the aggressive-age rule wins once old enough.
    life = Lifecycle(
        catalog,
        [
            Rule("videos/", Action.EXPIRE, older_than=100),
            Rule("videos/", Action.TRANSITION_COLD, older_than=30),
        ],
    )

    clock.advance(31)
    assert life.run() == [("videos/a.mp4", "-> cold")]  # step 1: cold

    clock.advance(80)  # now 111 idle
    assert life.run() == [("videos/a.mp4", "expired")]  # step 2: gone
    assert catalog.info(BUCKET, "videos/a.mp4") is None


def test_run_is_idempotent(cat):
    catalog, clock = cat
    catalog.put(BUCKET, "videos/a.mp4", b"x")
    life = Lifecycle(catalog, [Rule("videos/", Action.TRANSITION_COLD, older_than=30)])

    clock.advance(31)
    assert life.run() == [("videos/a.mp4", "-> cold")]
    # Converged: a second pass with the same clock does nothing.
    assert life.run() == []


def test_rules_are_scoped_by_prefix(cat):
    catalog, clock = cat
    catalog.put(BUCKET, "videos/keep.mp4", b"keep")
    catalog.put(BUCKET, "tmp/drop", b"drop")
    life = Lifecycle(catalog, [Rule("tmp/", Action.EXPIRE, older_than=10)])

    clock.advance(11)
    report = life.run()

    assert report == [("tmp/drop", "expired")]
    assert catalog.info(BUCKET, "videos/keep.mp4") is not None  # untouched
