"""The flat key -> bytes store. What R2/S3 is underneath the API.

There are no directories here. A key like "videos/clip.mp4" is one opaque
string; the "/" is just a character. We happen to map it onto nested files on
local disk for convenience, but the model is a flat dictionary:

    (bucket, key) -> bytes

Objects are immutable in spirit: to "change" one you overwrite the whole thing.
"""

from __future__ import annotations

from pathlib import Path


class Store:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, bucket: str, key: str) -> Path:
        # The key is opaque, but we must not let it escape the bucket dir
        # (e.g. key="../../etc/passwd"). Resolve and confirm containment.
        base = (self.root / bucket).resolve()
        target = (base / key).resolve()
        if base != target and base not in target.parents:
            raise ValueError("key escapes bucket")
        return target

    def put(self, bucket: str, key: str, data: bytes) -> None:
        path = self._path(bucket, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)  # overwrite whole object

    def get(self, bucket: str, key: str) -> bytes | None:
        path = self._path(bucket, key)
        return path.read_bytes() if path.exists() else None

    def delete(self, bucket: str, key: str) -> bool:
        # Deleting a key removes the object entirely -- there is no "trash".
        # Returns whether something was actually there. Used by lifecycle
        # expiry and by tier transitions (delete-after-copy).
        path = self._path(bucket, key)
        if path.exists():
            path.unlink()
            return True
        return False
