"""Presigned URLs: granting capability by signature, not by credential.

This is the heart of the lab. A presigned URL lets a client that holds NO
secret talk directly to storage, for a limited time, on exactly one object.

The whole mechanism is one idea:

    The server (which holds the secret) computes an HMAC over a fixed
    "sentence" describing the request. The client carries that HMAC in the
    URL. The storage service (which holds the SAME secret) recomputes the
    HMAC and compares. Match + not expired => allow.

Nothing here is specific to our toy. Real S3/R2 SigV4 is a bigger version of
the same three functions: build a canonical string, HMAC it with the secret,
verify by recomputation.
"""

from __future__ import annotations

import hashlib
import hmac


def canonical_string(method: str, bucket: str, key: str, expires: int) -> str:
    """The exact bytes both sides sign.

    Signer and verifier MUST build a byte-identical string or the HMACs will
    never match. So the format is fixed and boring on purpose: method, the
    object's path, and the expiry -- each on its own line.

    Note `expires` is INSIDE the signed string. That is why a client cannot
    extend its own deadline: changing the expiry in the URL invalidates the
    signature.
    """
    return f"{method}\n/{bucket}/{key}\nexpires={int(expires)}"


def sign(secret: str, method: str, bucket: str, key: str, expires: int) -> str:
    """HMAC-SHA256 the canonical string with the secret.

    Why HMAC and not a plain hash like sha256(sentence)? A plain hash is
    forgeable: anyone can hash any sentence. HMAC folds the secret into the
    hash, so only a holder of the secret can produce a valid tag -- and the
    tag leaks nothing about the secret.
    """
    message = canonical_string(method, bucket, key, expires).encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def presign_url(
    base_url: str,
    secret: str,
    method: str,
    bucket: str,
    key: str,
    ttl: int,
    now: float,
) -> str:
    """The APP-SERVER role: mint a URL a credential-less client can use.

    In your real system this runs on your backend, which holds the R2 secret.
    It returns a plain URL. The client never sees the secret -- only the
    signature, which is a dead end (HMAC is one-way).
    """
    expires = int(now) + ttl
    sig = sign(secret, method, bucket, key, expires)
    return f"{base_url}/{bucket}/{key}?expires={expires}&sig={sig}"


def verify(
    secret: str,
    method: str,
    bucket: str,
    key: str,
    expires,
    sig,
    now: float,
) -> tuple[bool, str]:
    """The STORAGE role (what R2 does on every request): recompute and compare.

    Two independent checks, both required:
      1. Not expired -- the deadline the signer baked in has not passed.
      2. Signature matches -- recomputing the HMAC over THIS request's
         method/bucket/key/expires reproduces the tag in the URL.

    Because the key is part of the signed string, swapping the key in the URL
    (keeping the old signature) fails check 2. Because expires is signed too,
    editing it fails check 2 as well.
    """
    try:
        exp = int(expires)
    except (TypeError, ValueError):
        return False, "bad expires"

    if exp < int(now):
        return False, "expired"

    expected = sign(secret, method, bucket, key, exp)
    # Constant-time compare: a normal `==` on strings can leak, via timing,
    # how many leading bytes were correct, letting an attacker guess the tag
    # byte by byte. compare_digest takes the same time regardless.
    if not hmac.compare_digest(expected, sig or ""):
        return False, "bad signature"

    return True, "ok"
