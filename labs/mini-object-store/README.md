# mini-object-store

A tiny, readable object store that rebuilds the three mechanisms behind
Cloudflare R2 and Amazon S3 — **presigned URLs**, **multipart upload**, and
**lifecycle/tiering** — with nothing hidden behind a framework.

## Black Box

Three questions every real object store answers, rebuilt here from `hmac`,
`http.server`, and `hashlib`:

1. How can a client holding **no secret** upload/download directly from storage,
   for a limited time, on exactly one object? → **presigned URLs**
2. How does a **300 MB video** upload reliably over a flaky connection without
   starting over on every drop? → **multipart upload**
3. How do objects **automatically** move to cheaper cold storage when idle and
   expire when old, with no one running a script? → **lifecycle/tiering**

## Smallest Build

**Step 1 — presigned URLs.** Three roles, one idea (HMAC over a fixed string):

| Role | Code | Holds secret? |
| --- | --- | --- |
| App server (mints URLs) | `signing.presign_url` | yes |
| Client (uses URLs) | the demo / your browser | **no** |
| Storage (verifies) | `server.py` | yes |

- `signing.py` — build a canonical string, HMAC it, verify by recomputation. **The heart.**
- `store.py` — the flat `(bucket, key) -> bytes` store. No directories; `/` is just a character.
- `server.py` — an HTTP service that verifies the signature, then reads/writes. Plays R2's role.
- `demo.py` — narrates the flow end to end.

**Step 2 — multipart upload.** A big write becomes many small idempotent writes
plus an ordered manifest.

- `multipart.py` — `initiate → upload_part → complete → abort`, with S3's
  `md5(part md5s)-N` ETag. Parts arrive in any order; the manifest imposes order
  at commit; a retried part just overwrites.
- `demo_multipart.py` — splits a file, uploads out of order, retries one part, reassembles.

**Step 3 — lifecycle / tiering.** A stateless reconciliation loop: rules declare
where objects should end up; a scan converges.

- `lifecycle.py` — `Catalog` (metadata + hot/cold physical tiers) + `Lifecycle`
  (prefix-scoped transition/expire rules). "Idle" is measured from last access;
  a read resets it. Going cold physically moves the bytes.
- `demo_lifecycle.py` — objects age hot → cold → expired across timed passes.

Not built yet: real SigV4 (headers/region/date), auto-abort of stale multipart
uploads, and the real-system migration (point the TikTok analyzer at R2).

## Reference Alignment

R2 and S3 are **S3-compatible**, so each mechanism maps onto the real thing;
`notes/references.md` records the exact simplifications.

- Presign: simplified `SigV4` — canonical request → HMAC → verify by
  recomputation. Real S3 signs more fields (headers, region, date).
- Multipart: mirrors `initiate/upload_part/complete/abort` and the
  `md5(part md5s)-N` ETag.
- Lifecycle: mirrors S3 lifecycle config (prefix-scoped transition/expire);
  R2 itself has a single tier, so tiering is where the toy teaches S3, not R2.

Links: [SigV4](https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-query-string-auth.html)
· [R2 S3 API](https://developers.cloudflare.com/r2/api/s3/)
· [multipart](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html)
· [lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)

## Run

```bash
cd labs/mini-object-store
PYTHONPATH=src python3 -m mini_object_store.demo             # presigned URLs
PYTHONPATH=src python3 -m mini_object_store.demo_multipart   # multipart upload
PYTHONPATH=src python3 -m mini_object_store.demo_lifecycle   # lifecycle/tiering
```

## Verify

```bash
cd labs/mini-object-store
python3 -m pytest
```

19 tests pin the mechanisms: no-credential round trip + tamper/expiry/wrong-secret
rejected (presign); byte-identical reassembly, out-of-order parts, idempotent
retry, corrupt-manifest rejection, no-object-until-complete (multipart);
hot→cold physical move, idle-clock reset on read, expiry, and convergence
(lifecycle).

## Done Gates

- [x] Runnable (`demo.py`, `demo_multipart.py`, `demo_lifecycle.py`)
- [x] Verifiable (`pytest`, 19 tests)
- [x] Aligned (simplified S3 SigV4 / multipart / lifecycle)
- [x] Explainable (`notes/explain.md`)
- [x] Compressed (`notes/principles.md`)
