# Explain It Simply

A presigned URL is a **capability**: a link that IS permission to do one thing.

The trick is HMAC. The app server (which knows the secret) writes down a short
fixed sentence describing the request:

    PUT
    /videos/clip.mp4
    expires=1783655420

It HMACs that sentence with the secret and staples the result to the URL as
`&sig=...`. The client gets only the URL — never the secret — and sends its
request straight to storage. Storage knows the same secret, rebuilds the exact
same sentence from the incoming request, HMACs it, and compares.

- Match + not expired -> allow.
- Anything about the request changed (the key, the method, the expiry)? The
  rebuilt sentence differs, the HMAC differs, and it is rejected.

Why it holds:

- **HMAC is one-way**, so the signature never leaks the secret.
- **The expiry is inside the signed sentence**, so a client cannot extend its
  own deadline.
- **The key is inside the signed sentence**, so a signature for `clip.mp4`
  cannot be reused for `someone-else.mp4`.

That is the entire security model of direct upload/download in object storage.
