"""Multipart tests: prove the mechanism, not the happy path only.

Each test pins one property that is the *reason* multipart exists:
byte-identity after reassembly, order-by-manifest (not by arrival), idempotent
retry, integrity rejection, and no-object-until-complete.
"""

import pytest

from mini_object_store import Multipart, Store, combined_etag, split

BUCKET = "media"
KEY = "videos/big.mp4"


@pytest.fixture
def mp(tmp_path):
    return Multipart(Store(tmp_path / "data"))


def _upload_all(mp, parts):
    """Upload parts in the given order; return the ordered manifest by part no."""
    upload_id = mp.initiate(BUCKET, KEY)
    manifest = []
    for part_number, chunk in parts:
        etag = mp.upload_part(upload_id, part_number, chunk)
        manifest.append((part_number, etag))
    manifest.sort(key=lambda pe: pe[0])  # manifest is ordered by part number
    return upload_id, manifest


def test_reassembly_is_byte_identical(mp):
    original = b"".join(bytes([i % 256]) * 1000 for i in range(10))  # 10 KB
    chunks = split(original, part_size=1024)
    upload_id, manifest = _upload_all(mp, list(enumerate(chunks, start=1)))

    mp.complete(upload_id, manifest)

    assert mp.store.get(BUCKET, KEY) == original


def test_parts_arriving_out_of_order_still_assemble_correctly(mp):
    # The whole point: parts race in over parallel connections. Arrival order
    # must not decide byte order -- the manifest does.
    chunks = [b"AAAA", b"BBBB", b"CCCC", b"DDDD"]
    scrambled = [(3, chunks[2]), (1, chunks[0]), (4, chunks[3]), (2, chunks[1])]
    upload_id, manifest = _upload_all(mp, scrambled)

    mp.complete(upload_id, manifest)

    assert mp.store.get(BUCKET, KEY) == b"AAAABBBBCCCCDDDD"


def test_reuploading_a_part_is_idempotent(mp):
    upload_id = mp.initiate(BUCKET, KEY)
    mp.upload_part(upload_id, 1, b"first-try-garbled")
    # Client wasn't sure part 1 landed cleanly, so it retries the same part.
    good = mp.upload_part(upload_id, 1, b"HELLO")
    tail = mp.upload_part(upload_id, 2, b"WORLD")

    mp.complete(upload_id, [(1, good), (2, tail)])

    assert mp.store.get(BUCKET, KEY) == b"HELLOWORLD"


def test_corrupted_manifest_etag_is_rejected(mp):
    upload_id = mp.initiate(BUCKET, KEY)
    mp.upload_part(upload_id, 1, b"HELLO")
    mp.upload_part(upload_id, 2, b"WORLD")

    with pytest.raises(ValueError, match="etag mismatch"):
        mp.complete(upload_id, [(1, "deadbeef"), (2, "cafebabe")])

    # Nothing was committed under the key.
    assert mp.store.get(BUCKET, KEY) is None


def test_missing_part_is_rejected(mp):
    upload_id = mp.initiate(BUCKET, KEY)
    etag = mp.upload_part(upload_id, 1, b"HELLO")

    with pytest.raises(ValueError, match="never uploaded"):
        mp.complete(upload_id, [(1, etag), (2, "whatever")])

    assert mp.store.get(BUCKET, KEY) is None


def test_object_does_not_exist_until_complete(mp):
    upload_id = mp.initiate(BUCKET, KEY)
    mp.upload_part(upload_id, 1, b"HELLO")
    # Uploaded a part, but never completed.
    assert mp.store.get(BUCKET, KEY) is None


def test_abort_leaves_no_object_and_no_staging(mp):
    upload_id = mp.initiate(BUCKET, KEY)
    mp.upload_part(upload_id, 1, b"HELLO")

    mp.abort(upload_id)

    assert mp.store.get(BUCKET, KEY) is None
    assert not (mp.staging / upload_id).exists()


def test_completed_etag_has_part_count_suffix(mp):
    upload_id = mp.initiate(BUCKET, KEY)
    e1 = mp.upload_part(upload_id, 1, b"HELLO")
    e2 = mp.upload_part(upload_id, 2, b"WORLD")

    etag = mp.complete(upload_id, [(1, e1), (2, e2)])

    # The S3 signature: a hash of the part hashes, suffixed with the count.
    assert etag == combined_etag([e1, e2])
    assert etag.endswith("-2")
