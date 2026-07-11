# Principles

## Capability by signature, not by credential

The transferable idea, far bigger than object storage: instead of handing out a
secret (which can do anything, forever), hand out a **signature over a specific,
expiring statement**. The holder can do exactly what was signed, until it
expires, and nothing more. JWTs, signed cookies, capability URLs, and S3/R2
presigned URLs are all this one pattern.

## Verify by recomputation

The verifier stores no per-URL state. It re-derives the expected signature from
the request in front of it and compares. Statelessness is why storage can
verify billions of independent presigned URLs without a database of them.

## Sign everything that must not change

Whatever you put inside the signed string becomes tamper-evident: method, key,
expiry. Whatever you leave out is free to vary. Deciding what goes into the
canonical string IS the security design.

## A big write is many small idempotent writes plus an ordered manifest

Multipart upload is not a special "big file" feature bolted on -- it is the
general shape of doing a large operation reliably over an unreliable channel.
Split the work into parts, make each part idempotent (retry = overwrite, no
side effect), and defer ordering to a manifest applied at the very end. The
transferable idea: **never make a long operation all-or-nothing on a flaky
line; make it a set of retryable pieces plus a final commit.** Resumable
downloads, chunked file sync, and DB write-ahead logs are the same shape.

The commit is atomic from the outside: before `complete()` the object does not
exist under its key; after it, the whole object exists. Parts staged and then
abandoned cost money but are invisible -- which is exactly why real S3 needs
lifecycle rules to auto-abort stale uploads.

A multipart ETag is `md5(concat of the part md5s)-N`, NOT the md5 of the file.
That surprises everyone once. The reason is the same principle: storage tags
the object from the PART hashes, so it never has to hold the whole file at once
to know its identity.

## Lifecycle is a reconciliation loop, not a daemon watching each object

Automatic tiering and expiry are not "an alarm per object." They are a loop:
declare rules for where objects SHOULD end up, periodically scan actual state,
apply the next step, stop when nothing is left to do. Run it again and it does
nothing -- it has converged. It keeps no "already handled" memory; it re-derives
the right action every pass from timestamps + rules. This is the same shape as a
Kubernetes controller and a garbage collector. **Desired state as rules + scan
actual + converge** is the transferable idea; storage lifecycle is just one
instance.

"Idle", not "old", drives it: the clock is measured from last_accessed, and a
read resets it. That is the whole definition of hot vs cold made mechanical --
touched recently = hot = worth keeping on fast storage.

A tier is a label AND a location. Going cold physically copies the bytes to a
cheaper store and deletes the hot copy; the catalog records which tier holds
them so reads still resolve. "Cold is cheaper" is physical, not accounting.

## Storage is a flat, immutable KV; the database holds the keys

There are no directories — `videos/clip.mp4` is one opaque key. To change an
object you overwrite the whole thing. Your application database stores the
**key** (a string), never the bytes.
