"""End-to-end narration of the presigned-URL flow, showing the three roles.

Run:  python -m mini_object_store.demo

    APP SERVER  holds the secret, mints URLs        (your TikTok backend)
    CLIENT      holds NO secret, uses the URLs       (a browser / a worker)
    STORAGE     holds the secret, verifies signatures (R2)
"""

from __future__ import annotations

import threading
import time
import urllib.error
import urllib.request

from .server import make_server
from .signing import presign_url

# Talk to localhost directly; ignore any HTTP(S) proxy in the environment.
_open = urllib.request.build_opener(urllib.request.ProxyHandler({})).open


def main():  # pragma: no cover - manual narration
    secret = "shared-account-secret"  # known to APP SERVER and STORAGE only

    # STORAGE (R2's role): start it in the background.
    server = make_server(root="./.mos-data", secret=secret)
    host, port = server.server_address
    base = f"http://{host}:{port}"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"[storage] listening on {base}\n")

    now = time.time()

    # APP SERVER: mint a presigned PUT. This is the only place the secret lives.
    upload_url = presign_url(base, secret, "PUT", "videos", "clip.mp4", ttl=60, now=now)
    print(f"[app]    minted upload URL:\n         {upload_url}")
    print(f"[app]    secret leaked into URL? {'shared-account-secret' in upload_url}\n")

    # CLIENT: upload straight to storage with NO credential in the request.
    req = urllib.request.Request(upload_url, data=b"pretend-video-bytes", method="PUT")
    print(f"[client] PUT -> {_open(req).read().decode()}\n")

    # APP SERVER: mint a presigned GET so someone can watch it.
    download_url = presign_url(base, secret, "GET", "videos", "clip.mp4", ttl=60, now=now)

    # CLIENT: download it, again with no credential.
    data = _open(download_url).read()
    print(f"[client] GET  -> {data!r}\n")

    # ATTACKER: keep the valid signature but point it at another object.
    tampered = upload_url.replace("videos/clip.mp4", "videos/someone-else.mp4")
    try:
        _open(urllib.request.Request(tampered, data=b"x", method="PUT"))
    except urllib.error.HTTPError as e:
        print(f"[attack] tampered key rejected: {e.code} {e.read().decode()}")


if __name__ == "__main__":
    main()
