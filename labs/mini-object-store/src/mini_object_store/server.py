"""A minimal storage service that plays R2's role.

It holds the secret and does ONE job on every request: verify the presigned
signature, then read or write the flat store. No secret, valid signature, or
fresh deadline -> 403. That is the entire access-control model of presigned
object storage, with nothing hidden.

    PUT /<bucket>/<key>?expires=...&sig=...   -> store bytes
    GET /<bucket>/<key>?expires=...&sig=...   -> return bytes
"""

from __future__ import annotations

import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from .signing import verify
from .store import Store


def make_handler(store: Store, secret: str, clock=time.time):
    class Handler(BaseHTTPRequestHandler):
        def _authorized(self):
            parsed = urlparse(self.path)
            parts = parsed.path.lstrip("/").split("/", 1)
            if len(parts) != 2 or not parts[1]:
                self._respond(400, b"path must be /<bucket>/<key>")
                return None
            bucket, key = parts
            query = parse_qs(parsed.query)
            expires = query.get("expires", [""])[0]
            sig = query.get("sig", [""])[0]
            ok, reason = verify(
                secret, self.command, bucket, key, expires, sig, now=clock()
            )
            if not ok:
                self._respond(403, reason.encode())
                return None
            return bucket, key

        def do_PUT(self):
            checked = self._authorized()
            if not checked:
                return
            bucket, key = checked
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            store.put(bucket, key, body)
            self._respond(200, b"stored")

        def do_GET(self):
            checked = self._authorized()
            if not checked:
                return
            bucket, key = checked
            data = store.get(bucket, key)
            if data is None:
                self._respond(404, b"no such object")
                return
            self._respond(200, data)

        def _respond(self, code: int, body: bytes):
            self.send_response(code)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # keep the demo/test output clean
            pass

    return Handler


def make_server(root, secret: str, host="127.0.0.1", port=0, clock=time.time):
    """Build (but do not start) the HTTP server. port=0 picks a free port."""
    return HTTPServer((host, port), make_handler(Store(root), secret, clock))


def main():  # pragma: no cover - manual runner
    import os
    import tempfile

    secret = os.environ.get("MOS_SECRET", "dev-secret")
    root = os.environ.get("MOS_ROOT", tempfile.mkdtemp(prefix="mos-"))
    server = make_server(root, secret, port=int(os.environ.get("MOS_PORT", "8010")))
    host, port = server.server_address
    print(f"mini-object-store on http://{host}:{port}  (root={root})")
    server.serve_forever()


if __name__ == "__main__":  # pragma: no cover
    main()
