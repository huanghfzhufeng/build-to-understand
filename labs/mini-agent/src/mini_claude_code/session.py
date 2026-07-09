from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class SessionLog:
    """Append-only JSONL trace of what the agent did."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: str, payload: Any) -> None:
        record = {
            "time": datetime.now(UTC).isoformat(),
            "event": event,
            "payload": self._to_jsonable(payload),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _to_jsonable(self, value: Any) -> Any:
        if hasattr(value, "__dataclass_fields__"):
            return self._to_jsonable(asdict(value))
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, dict):
            return {key: self._to_jsonable(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._to_jsonable(item) for item in value]
        return value
