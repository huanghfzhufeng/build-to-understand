"""Narrated multipart upload: watch a big file become parts and come back whole.

Run:  PYTHONPATH=src python3 -m mini_object_store.demo_multipart

It plays the CLIENT and the STORAGE roles and prints what each does, so the
mechanism -- split, upload out of order, retry one part, assemble by manifest --
is visible instead of hidden inside an SDK.
"""

from __future__ import annotations

import tempfile

from .multipart import Multipart, combined_etag, split
from .store import Store

BUCKET = "media"
KEY = "videos/big.mp4"
PART_SIZE = 5  # tiny on purpose so the parts are easy to read


def main() -> None:
    store = Store(tempfile.mkdtemp(prefix="mos-mp-"))
    mp = Multipart(store)

    original = b"THE-QUICK-BROWN-FOX-JUMPS-OVER"  # our "big video"
    print("CLIENT   has a file:", original.decode(), f"({len(original)} bytes)")

    chunks = split(original, PART_SIZE)
    print(f"CLIENT   splits into {len(chunks)} parts of <= {PART_SIZE} bytes:")
    for n, c in enumerate(chunks, start=1):
        print(f"           part {n}: {c.decode()!r}")

    upload_id = mp.initiate(BUCKET, KEY)
    print("\nSTORAGE  opened upload:", upload_id, "(no object exists yet)")
    print("           get() now ->", mp.store.get(BUCKET, KEY))

    # Upload OUT OF ORDER, the way parallel connections finish at random.
    order = [3, 1, 5, 2, 6, 4][: len(chunks)]
    manifest: dict[int, str] = {}
    print("\nCLIENT   uploads parts out of order:", order)
    for n in order:
        etag = mp.upload_part(upload_id, n, chunks[n - 1])
        manifest[n] = etag
        print(f"           sent part {n} -> etag {etag[:8]}…")

    # One part looked corrupt on the client's checksum; retry just that part.
    print("\nCLIENT   part 2 checksum looked off -> retry ONLY part 2 (idempotent)")
    manifest[2] = mp.upload_part(upload_id, 2, chunks[1])
    print(f"           re-sent part 2 -> etag {manifest[2][:8]}… (overwrote, safe)")

    ordered = [(n, manifest[n]) for n in sorted(manifest)]
    print("\nCLIENT   sends the MANIFEST (ordered part list):")
    for n, e in ordered:
        print(f"           {n}: {e[:8]}…")

    etag = mp.complete(upload_id, ordered)
    print("\nSTORAGE  validated every part, concatenated by manifest order.")
    print("           final object etag:", etag, "  <- note the '-N' suffix")
    print("           etag == md5(part md5s)+count ?",
          etag == combined_etag([e for _, e in ordered]))

    result = mp.store.get(BUCKET, KEY)
    print("\nRESULT   reassembled bytes:", result.decode())
    print("           byte-identical to original?", result == original)


if __name__ == "__main__":  # pragma: no cover
    main()
