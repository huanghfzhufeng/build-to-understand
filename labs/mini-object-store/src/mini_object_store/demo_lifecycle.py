"""Narrated lifecycle: watch objects age from hot -> cold -> expired.

Run:  PYTHONPATH=src python3 -m mini_object_store.demo_lifecycle

A controllable clock fast-forwards "days" so you can see the reconciliation
loop take one step each pass and then converge.
"""

from __future__ import annotations

import tempfile

from .lifecycle import Action, Catalog, Lifecycle, Rule, Tier
from .store import Store

BUCKET = "media"


class Clock:
    def __init__(self, t: float = 0.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, days: float) -> None:
        self.t += days * 86400


def snapshot(catalog: Catalog) -> str:
    rows = []
    for i in catalog.objects():
        rows.append(f"{i.key} [{i.tier.value}]")
    return ", ".join(rows) if rows else "(no objects)"


def main() -> None:
    clock = Clock()
    root = tempfile.mkdtemp(prefix="mos-life-")
    catalog = Catalog(Store(f"{root}/hot"), Store(f"{root}/cold"), clock=clock)

    # Policy: videos go cold after 30 idle days, expire after 365.
    #         tmp files are thrown away after 1 day.
    life = Lifecycle(
        catalog,
        [
            Rule("videos/", Action.EXPIRE, older_than=365 * 86400),
            Rule("videos/", Action.TRANSITION_COLD, older_than=30 * 86400),
            Rule("tmp/", Action.EXPIRE, older_than=1 * 86400),
        ],
    )

    catalog.put(BUCKET, "videos/viral.mp4", b"a hit that stays hot")
    catalog.put(BUCKET, "videos/old.mp4", b"nobody watches this")
    catalog.put(BUCKET, "tmp/upload.part", b"scratch")
    print("day   0  put 3 objects:", snapshot(catalog))

    # Day 2: the viral one keeps getting watched; tmp scratch ages out.
    clock.advance(2)
    catalog.get(BUCKET, "videos/viral.mp4")  # a view resets its idle clock
    print(f"day   2  a viewer watches viral.mp4 (resets its clock)")
    print("day   2  lifecycle run ->", life.run() or "nothing", "|", snapshot(catalog))

    # Day 40: old.mp4 has been idle 40 days -> cold. viral watched at day 2,
    # idle 38 days -> also cold (nobody watched it since).
    clock.advance(38)
    print(f"\nday  40  lifecycle run ->", life.run(), "|", snapshot(catalog))
    print("           old.mp4 bytes now live in the COLD store:",
          catalog.cold.get(BUCKET, "videos/old.mp4") is not None)

    # Day 400: old.mp4 crosses the 365-day expiry -> deleted.
    clock.advance(360)
    print(f"\nday 400  lifecycle run ->", life.run(), "|", snapshot(catalog))

    # Run again same day: converged, nothing left to do.
    print("day 400  run again    ->", life.run() or "nothing (converged)")

    print("\nPRINCIPLE  rules declare the destination; the loop just takes the")
    print("           next step each pass and stops when nothing is left to do.")


if __name__ == "__main__":  # pragma: no cover
    main()
