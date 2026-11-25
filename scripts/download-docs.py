#!/usr/bin/env python3
"""Download the README media from the upstream repository."""

from __future__ import annotations

import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MANIFEST = Path("/private/tmp/word-atlas-docs-assets.json")
OUTPUT = Path("docs/assets")


def fetch(item: dict) -> None:
    destination = OUTPUT / item["name"]
    if destination.exists() and destination.stat().st_size == item["size"]:
        return
    with urllib.request.urlopen(item["download_url"], timeout=60) as response:
        data = response.read()
    if len(data) != item["size"]:
        raise IOError(f"{item['name']}: {len(data)}/{item['size']} bytes")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    print(item["name"], flush=True)


def main() -> None:
    items = json.loads(MANIFEST.read_text())
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(fetch, items))


if __name__ == "__main__":
    main()
