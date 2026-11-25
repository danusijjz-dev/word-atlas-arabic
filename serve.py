#!/usr/bin/env python3
"""Local server with gzip and byte ranges for the built Word Atlas site."""

from __future__ import annotations

import gzip
import io
import mimetypes
import os
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent / "dist"
PORT = int(os.environ.get("PORT", "5188"))
COMPRESSIBLE = {".html", ".css", ".js", ".json", ".webmanifest", ".svg", ".txt"}
MEDIA = {".mp3", ".mp4", ".webp", ".png", ".jpg"}


class AtlasHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _cache_header(self, file: Path) -> str:
        return "public, max-age=604800, immutable" if "/atlas/img/" in file.as_posix() or "/atlas/thumb/" in file.as_posix() or "/atlas/audio/" in file.as_posix() else "no-cache"

    def send_head(self):
        file = Path(self.translate_path(urlsplit(self.path).path))
        if file.is_dir():
            file /= "index.html"
        if not file.is_file():
            self.send_error(404)
            return None

        suffix = file.suffix.lower()
        cache = self._cache_header(file)
        range_header = self.headers.get("Range")
        if range_header and suffix in MEDIA:
            size = file.stat().st_size
            match = re.match(r"bytes=(\d+)-(\d*)", range_header)
            if not match:
                self.send_error(416)
                return None
            start = int(match.group(1))
            end = min(int(match.group(2) or size - 1), size - 1)
            if start > end or start >= size:
                self.send_error(416)
                return None
            self.send_response(206)
            self.send_header("Content-Type", mimetypes.guess_type(file.name)[0] or "application/octet-stream")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Cache-Control", cache)
            self.end_headers()
            stream = file.open("rb")
            stream.seek(start)
            self.range_remaining = end - start + 1
            self.range_stream = stream
            return None

        data = file.read_bytes()
        if "gzip" in self.headers.get("Accept-Encoding", "") and suffix in COMPRESSIBLE:
            data = gzip.compress(data, compresslevel=6)
            self.send_response(200)
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
        else:
            self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(file.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        return io.BytesIO(data)

    def do_GET(self):
        body = self.send_head()
        if getattr(self, "range_stream", None):
            try:
                while self.range_remaining > 0:
                    chunk = self.range_stream.read(min(64 * 1024, self.range_remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.range_remaining -= len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                self.range_stream.close()
                self.range_stream = None
        elif body:
            try:
                self.copyfile(body, self.wfile)
            finally:
                body.close()


if __name__ == "__main__":
    print(f"Serving {ROOT}")
    print(f"http://127.0.0.1:{PORT}/#/atlas")
    ThreadingHTTPServer(("127.0.0.1", PORT), AtlasHandler).serve_forever()
