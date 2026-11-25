#!/usr/bin/env python3
"""Download the complete Word Atlas image/thumbnail/audio set from the official site."""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = "https://0xlei.tech/words/atlas"
MEDIA = {"uk": 2, "us": 4, "ex": 8, "ex2": 16}


def jobs(index_path: Path, output: Path) -> list[tuple[str, Path]]:
    atlas = json.loads(index_path.read_text())
    out: list[tuple[str, Path]] = []
    for row in atlas["words"]:
        ident, media = row[0], row[6]
        for size in ("img", "thumb"):
            out.append((f"{BASE}/{size}/{ident}.webp", output / size / f"{ident}.webp"))
        for kind, bit in MEDIA.items():
            if media & bit:
                out.append((f"{BASE}/audio/{kind}/{ident}.mp3", output / "audio" / kind / f"{ident}.mp3"))
    return out


def fetch(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size > 0:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Word-Atlas-Full-Copy/1.0"})
            with urllib.request.urlopen(request, timeout=45) as response:
                expected = response.headers.get("Content-Length")
                data = response.read()
            if expected and len(data) != int(expected):
                raise IOError(f"short response ({len(data)}/{expected})")
            if not data:
                raise IOError("empty response")
            if destination.suffix == ".webp" and not (data.startswith(b"RIFF") and data[8:12] == b"WEBP"):
                raise IOError("not a WebP image")
            if destination.suffix == ".mp3" and not (data.startswith(b"ID3") or data[:1] == b"\xff"):
                raise IOError("not an MP3 file")
            partial.write_bytes(data)
            os.replace(partial, destination)
            return
        except (OSError, urllib.error.URLError) as error:
            last_error = error
            time.sleep(0.35 * (attempt + 1))
    partial.unlink(missing_ok=True)
    raise RuntimeError(f"{url}: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, default=Path("public/atlas/index.json"))
    parser.add_argument("--output", type=Path, default=Path("public/atlas"))
    parser.add_argument("--workers", type=int, default=18)
    args = parser.parse_args()

    work = jobs(args.index, args.output)
    print(f"Media files: {len(work):,}")
    lock = threading.Lock()
    done = 0
    started = time.monotonic()

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(fetch, url, path) for url, path in work]
        for future in as_completed(futures):
            future.result()
            with lock:
                done += 1
                if done % 250 == 0 or done == len(work):
                    elapsed = max(1, time.monotonic() - started)
                    print(f"{done:,}/{len(work):,} · {done / elapsed:.1f} files/s", flush=True)

    print("Complete.")


if __name__ == "__main__":
    main()
