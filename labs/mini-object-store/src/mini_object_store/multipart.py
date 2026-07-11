"""Multipart upload: turning one big upload into many small idempotent writes.

The black box: how does object storage accept a 300 MB video over a flaky
connection without "start over from byte 0" every time it drops?

The whole mechanism is one idea:

    Split the object into parts. Upload each part on its own, in any order,
    retrying just the parts that fail. At the end, send a MANIFEST -- an
    ordered list of (part_number, etag) -- and storage concatenates the parts
    in that order into the final object.

Three properties fall out of that shape, and they are the reason multipart
exists:

  * Idempotent parts. Re-uploading part 7 just overwrites part 7. A retry is
    safe and cheap; nothing else is disturbed.
  * Order imposed at the end. Parts race in over parallel connections in
    whatever order they finish. The manifest -- not arrival order -- decides
    the byte layout of the final object.
  * Integrity per part and overall. Each part gets an ETag (a hash). The
    client checks each part landed intact; complete() re-checks the whole
    manifest before it commits. A corrupted or reordered manifest is rejected
    instead of silently producing a scrambled file.

This module deliberately keeps the parts on disk under a staging area and only
materializes the final object at complete(). Before complete(), the object does
not exist -- exactly like S3/R2, where an aborted or half-finished multipart
upload leaves no visible object (only chargeable staged parts).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from .store import Store


def _etag(data: bytes) -> str:
    """A part's ETag is just the hash of its bytes.

    Real S3 uses MD5 here. MD5 is broken for security, but an ETag is an
    integrity/version tag, not a signature -- it only has to detect accidental
    corruption and identify identical bytes, so MD5 is fine and we match S3.
    """
    return hashlib.md5(data).hexdigest()


def combined_etag(part_etags: list[str]) -> str:
    """Reproduce S3's peculiar multipart ETag: md5(concat of raw part md5s)-N.

    This is why a multipart object's ETag has a `-3` suffix and is NOT the md5
    of the whole file -- a fact that surprises everyone the first time they see
    it. The ETag is computed from the PART hashes, not the reassembled bytes,
    precisely because storage never has to hold the whole file at once to know
    its tag.
    """
    raw = b"".join(bytes.fromhex(e) for e in part_etags)
    return f"{hashlib.md5(raw).hexdigest()}-{len(part_etags)}"


@dataclass
class Upload:
    """Server-side state for one in-flight multipart upload."""

    upload_id: str
    bucket: str
    key: str
    # part_number -> etag of the bytes we have staged for it
    parts: dict[int, str] = field(default_factory=dict)


class Multipart:
    """The four S3 multipart operations, over a flat Store.

    Staged parts live under  <store.root>/_multipart/<upload_id>/<n>.part
    and are invisible as objects until complete() assembles them.
    """

    def __init__(self, store: Store) -> None:
        self.store = store
        self.staging = Path(store.root) / "_multipart"
        self.staging.mkdir(parents=True, exist_ok=True)
        # In real S3 this table is durable server state keyed by upload_id.
        self._uploads: dict[str, Upload] = {}
        self._counter = 0

    def initiate(self, bucket: str, key: str) -> str:
        """Open an upload and hand back an upload_id that ties the parts together.

        Note the object does NOT exist yet. We have only reserved a place to
        stage parts. Nothing is visible under (bucket, key) until complete().
        """
        self._counter += 1
        upload_id = f"upl-{self._counter}"
        self._uploads[upload_id] = Upload(upload_id, bucket, key)
        (self.staging / upload_id).mkdir(parents=True, exist_ok=True)
        return upload_id

    def upload_part(self, upload_id: str, part_number: int, data: bytes) -> str:
        """Stage one part. Idempotent: same part_number simply overwrites.

        This is the property that makes retries trivial -- a client that isn't
        sure whether part 7 landed can just send it again. Returns the part's
        ETag so the client can confirm the bytes arrived intact.
        """
        upload = self._require(upload_id)
        if part_number < 1:
            raise ValueError("part_number is 1-based")
        etag = _etag(data)
        (self.staging / upload_id / f"{part_number}.part").write_bytes(data)
        upload.parts[part_number] = etag  # overwrite on retry -> idempotent
        return etag

    def complete(self, upload_id: str, manifest: list[tuple[int, str]]) -> str:
        """Assemble the final object from an ORDERED manifest of (part, etag).

        The manifest is the client's declaration of intent: these parts, in
        this order, with these expected hashes. We validate before committing:

          * every named part was actually staged,
          * every etag matches what we staged (no corruption / wrong part),

        then concatenate in manifest order and write the whole object at once.
        Only now does it appear under (bucket, key). Finally we clean up the
        staging area -- the parts have served their purpose.
        """
        upload = self._require(upload_id)

        blobs: list[bytes] = []
        part_etags: list[str] = []
        for part_number, expected_etag in manifest:
            if part_number not in upload.parts:
                raise ValueError(f"part {part_number} was never uploaded")
            path = self.staging / upload_id / f"{part_number}.part"
            data = path.read_bytes()
            actual = _etag(data)
            if actual != expected_etag:
                # The manifest disagrees with the bytes we hold. Refuse rather
                # than build a file the client did not actually intend.
                raise ValueError(
                    f"part {part_number} etag mismatch: "
                    f"manifest {expected_etag} != staged {actual}"
                )
            blobs.append(data)
            part_etags.append(actual)

        self.store.put(upload.bucket, upload.key, b"".join(blobs))
        self._cleanup(upload_id)
        return combined_etag(part_etags)

    def abort(self, upload_id: str) -> None:
        """Throw the staged parts away without producing an object.

        A dropped or cancelled upload must leave no trace under (bucket, key).
        (In real S3 you pay for staged parts until you abort -- hence lifecycle
        rules that auto-abort stale multipart uploads.)
        """
        self._require(upload_id)
        self._cleanup(upload_id)

    # -- internals ---------------------------------------------------------

    def _require(self, upload_id: str) -> Upload:
        upload = self._uploads.get(upload_id)
        if upload is None:
            raise KeyError(f"no such upload: {upload_id}")
        return upload

    def _cleanup(self, upload_id: str) -> None:
        dir_ = self.staging / upload_id
        if dir_.exists():
            for part in dir_.iterdir():
                part.unlink()
            dir_.rmdir()
        self._uploads.pop(upload_id, None)


def split(data: bytes, part_size: int) -> list[bytes]:
    """Client-side helper: cut bytes into <= part_size chunks (1-based parts).

    Real clients stream from a file and never hold the whole thing in memory;
    we take bytes for a readable demo. The mechanism is identical.
    """
    if part_size < 1:
        raise ValueError("part_size must be positive")
    return [data[i : i + part_size] for i in range(0, len(data), part_size)] or [b""]
