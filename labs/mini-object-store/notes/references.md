# References

## Primary Sources

- AWS SigV4 query-string (presigned URL) auth:
  https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-query-string-auth.html
- Cloudflare R2 S3-compatible API:
  https://developers.cloudflare.com/r2/api/s3/
- Python `hmac` (constant-time compare, HMAC construction):
  https://docs.python.org/3/library/hmac.html

## Alignment Notes

This build is a simplified SigV4 presign:

```text
canonical string (method, key, expiry)
  -> HMAC-SHA256 with the secret
  -> verify by recomputation + expiry check
```

Real S3/R2 additionally sign headers, region, and a timestamp, and use a
derived signing key rather than the raw secret. The mechanism — sign a
canonical request, verify by recomputation — is the same. Because R2 speaks the
S3 API, the real client is `boto3`/any S3 SDK with the endpoint pointed at R2.

## Lifecycle / tiering (step 3, built)

- AWS S3 lifecycle configuration (transition + expiration rules):
  https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html
- S3 storage classes (Standard / IA / Glacier tiers):
  https://aws.amazon.com/s3/storage-classes/

Alignment: our `Lifecycle` mirrors real lifecycle config -- prefix-scoped rules
that transition or expire objects by age. Simplifications: idle is measured from
last_accessed (S3 transitions are from creation/modification; only Intelligent-
Tiering watches access), two tiers instead of the full Standard/IA/Glacier
ladder, and no per-tier retrieval latency/cost. R2 in reality has ONE tier, so
tiering is where the toy diverges from R2 most -- it teaches the S3 mechanism.
The idea -- rules declare the destination, a scan converges -- is faithful.

## Multipart upload (step 2, built)

- AWS multipart upload overview (initiate / upload part / complete / abort):
  https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html
- Cloudflare R2 multipart upload:
  https://developers.cloudflare.com/r2/objects/multipart-objects/

Alignment: our `Multipart` mirrors the four real operations and reproduces the
`md5(part md5s)-N` ETag. Simplifications vs real S3: upload_id is a counter (not
a signed opaque token), part-size minimums are not enforced (S3 requires >= 5
MiB for all parts except the last), and staged parts are not charged or
lifecycle-expired. The mechanism -- idempotent parts + ordered manifest +
validate-then-commit -- is faithful.
