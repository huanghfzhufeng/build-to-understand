"""Prove the presigned-URL mechanism over a real HTTP round trip.

The claim these tests make concrete:
  - a client with NO secret can upload and download, and
  - changing one character (the key, the expiry, the secret) is rejected.
When these pass, presigned URLs are no longer a concept -- you rebuilt them.
"""

import threading
import time
import urllib.error
import urllib.request

import pytest

from mini_object_store.server import make_server
from mini_object_store.signing import presign_url

SECRET = "shared-account-secret"

# Talk to localhost directly; ignore any HTTP(S) proxy in the environment.
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


@pytest.fixture
def base(tmp_path):
    server = make_server(tmp_path / "data", SECRET)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://{host}:{port}"
    server.shutdown()


def _put(url, data):
    return _opener.open(urllib.request.Request(url, data=data, method="PUT"))


def _get(url):
    return _opener.open(url)


def test_no_credential_roundtrip(base):
    now = time.time()
    up = presign_url(base, SECRET, "PUT", "videos", "clip.mp4", ttl=60, now=now)
    down = presign_url(base, SECRET, "GET", "videos", "clip.mp4", ttl=60, now=now)

    # The secret appears in NEITHER url the client holds.
    assert SECRET not in up
    assert SECRET not in down

    assert _put(up, b"pretend-video-bytes").status == 200
    assert _get(down).read() == b"pretend-video-bytes"


def test_tampered_key_rejected(base):
    now = time.time()
    up = presign_url(base, SECRET, "PUT", "videos", "clip.mp4", ttl=60, now=now)
    # Keep the valid signature, point it at a different object.
    tampered = up.replace("videos/clip.mp4", "videos/someone-else.mp4")
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        _put(tampered, b"x")
    assert excinfo.value.code == 403


def test_expired_rejected(base):
    now = time.time()
    # ttl negative -> the deadline is already in the past.
    url = presign_url(base, SECRET, "GET", "videos", "clip.mp4", ttl=-100, now=now)
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        _get(url)
    assert excinfo.value.code == 403


def test_wrong_secret_cannot_forge(base):
    now = time.time()
    # An attacker who guesses the secret wrong produces a wrong signature.
    url = presign_url(base, "wrong-guess", "GET", "videos", "clip.mp4", ttl=60, now=now)
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        _get(url)
    assert excinfo.value.code == 403
