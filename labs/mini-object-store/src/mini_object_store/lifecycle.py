"""Lifecycle & tiering: a stateless reconciliation loop over object metadata.

The black box: how does storage automatically move a video you haven't watched
in 30 days to cheaper "cold" storage, and delete it after a year -- without
anyone running a script by hand?

The mechanism is NOT a background daemon watching every object. It is a loop:

    1. Declare rules describing where objects SHOULD end up
       ("prefix videos/, not touched in 30 days -> cold";
        "prefix tmp/, older than 1 day -> expire").
    2. Periodically SCAN the actual objects.
    3. For each, apply the first matching rule to nudge it toward its target.

Run the loop again and nothing new happens -- it has converged. That is the
same shape as a Kubernetes controller or a garbage collector: desired state as
rules, actual state scanned, converge. Nothing here remembers "I already moved
this"; it re-derives the right action every pass. Statelessness again.

Two supporting ideas this file makes concrete:

  * A "tier" is a label PLUS a location. Going cold means the bytes physically
    move to a cheaper store; the catalog records which tier holds them so reads
    still find them. Hot vs cold is where the bytes live, not a mood.

  * The metadata lives apart from the bytes. The `Catalog` is the "database
    that holds the keys" from the presign lab, grown up: it also holds size,
    timestamps, and tier. The flat `Store`(s) hold only bytes. Lifecycle is
    pure metadata bookkeeping that occasionally moves or drops bytes.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum

from .store import Store


class Tier(str, Enum):
    HOT = "hot"  # recently used: fast store, higher price
    COLD = "cold"  # idle: cheap store, notionally slower to read


class Action(str, Enum):
    TRANSITION_COLD = "transition_cold"
    EXPIRE = "expire"  # delete the object entirely


@dataclass
class ObjectInfo:
    bucket: str
    key: str
    size: int
    created: float
    last_accessed: float
    tier: Tier = Tier.HOT


@dataclass
class Rule:
    """One line of policy: objects under `prefix`, idle >= `older_than`
    seconds, get `action` applied. `older_than` is measured from
    last_accessed -- "idle", not "old" -- which is what hot/cold really means.
    """

    prefix: str
    action: Action
    older_than: float


class Catalog:
    """Metadata table + two physical tiers (hot / cold Stores).

    put() lands in HOT and records metadata. get() reads from whichever tier
    currently holds the bytes and refreshes last_accessed -- touching an object
    resets its idle clock, which is exactly what keeps hot data hot.
    """

    def __init__(self, hot: Store, cold: Store, clock=time.time) -> None:
        self.hot = hot
        self.cold = cold
        self.clock = clock
        self._info: dict[tuple[str, str], ObjectInfo] = {}

    def _store_for(self, tier: Tier) -> Store:
        return self.hot if tier == Tier.HOT else self.cold

    def put(self, bucket: str, key: str, data: bytes) -> None:
        now = self.clock()
        self.hot.put(bucket, key, data)
        self._info[(bucket, key)] = ObjectInfo(
            bucket, key, len(data), created=now, last_accessed=now, tier=Tier.HOT
        )

    def get(self, bucket: str, key: str) -> bytes | None:
        info = self._info.get((bucket, key))
        if info is None:
            return None
        info.last_accessed = self.clock()  # a read resets the idle clock
        return self._store_for(info.tier).get(bucket, key)

    def info(self, bucket: str, key: str) -> ObjectInfo | None:
        return self._info.get((bucket, key))

    def objects(self) -> list[ObjectInfo]:
        return list(self._info.values())

    def transition(self, info: ObjectInfo, tier: Tier) -> None:
        """Move an object's bytes to another tier and update the label.

        Copy-then-delete: the bytes exist in exactly one tier before and after.
        This is why "cold storage is cheaper" is physical, not accounting --
        the bytes really sit in a different store.
        """
        if info.tier == tier:
            return
        src, dst = self._store_for(info.tier), self._store_for(tier)
        data = src.get(info.bucket, info.key)
        if data is not None:
            dst.put(info.bucket, info.key, data)
            src.delete(info.bucket, info.key)
        info.tier = tier

    def remove(self, bucket: str, key: str) -> None:
        info = self._info.pop((bucket, key), None)
        if info is not None:
            self._store_for(info.tier).delete(bucket, key)


@dataclass
class Lifecycle:
    """The reconciliation loop. `rules` are evaluated in order; the FIRST rule
    that matches an object wins for that pass.

    Order rules most-aggressive-age first (expire before transition), so an
    object progresses hot -> cold over early passes and is expired only once it
    is old enough for the expiry rule. Across successive runs the object walks
    its whole lifecycle; a single run only takes the next step.
    """

    catalog: Catalog
    rules: list[Rule]

    def run(self, now: float | None = None) -> list[tuple[str, str]]:
        """One scan. Returns a report of [(key, what happened)]. Idempotent:
        running again with the same clock produces an empty report -- the
        system has converged."""
        moment = self.catalog.clock() if now is None else now
        report: list[tuple[str, str]] = []
        for info in self.catalog.objects():
            for rule in self.rules:
                if not info.key.startswith(rule.prefix):
                    continue
                if moment - info.last_accessed < rule.older_than:
                    continue
                if rule.action == Action.EXPIRE:
                    self.catalog.remove(info.bucket, info.key)
                    report.append((info.key, "expired"))
                    break  # object is gone; no further rules apply
                if rule.action == Action.TRANSITION_COLD:
                    if info.tier != Tier.COLD:
                        self.catalog.transition(info, Tier.COLD)
                        report.append((info.key, "-> cold"))
                    break  # first matching rule wins this pass
        return report
