# Failures

## 502 instead of the expected 403/200 in tests

First `pytest` run: every request to `http://127.0.0.1:<port>` came back
`502 Bad Gateway`. Cause: the environment sets an HTTP(S) proxy, and
`urllib.request.urlopen` honors it — so requests to localhost were routed
through the proxy, which failed. Fix: build an opener with an empty
`ProxyHandler({})` so localhost is contacted directly. Applied in both the
tests and `demo.py`.

Lesson: "connection failed" was not a bug in the signing mechanism at all — the
signature layer was fine; the transport was being hijacked. Read the status
code: `502` is a gateway/proxy story, not a `403` auth story.

## Things deliberately NOT built yet

- Real SigV4 (headers, region, date in the canonical request). The toy signs
  only method/key/expiry; enough to see the mechanism, not wire-compatible with
  real S3.
- Auto-abort of stale multipart uploads. The lifecycle loop only reconciles
  finished objects; staged multipart parts have no timestamps yet, so a real
  "abort uploads older than N days" rule is left for later.
- The real-system migration: pointing the TikTok analyzer at R2 (store the key
  in the DB, serve via presigned GET). That is the payoff step, not yet done.
