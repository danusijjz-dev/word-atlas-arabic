#!/usr/bin/env python3
"""Prepare English source text and apply offline Arabic translations to entries."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = ROOT / "public/atlas/entries"
SOURCES = Path("/private/tmp/arabic-example-sources.json")
TRANSLATIONS = Path("/private/tmp/arabic-example-translations.json")
VOCALIZED = Path("/private/tmp/arabic-example-vocalized.txt")
DIACRITIC = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
ARABIC = re.compile(r"[\u0600-\u06ff]")


def collocation_parts(value: str) -> tuple[str, str]:
    parts = value.split("｜")
    return (parts[0].strip(), parts[1].strip() if len(parts) > 1 else "")


def prepare() -> None:
    sources: set[str] = set()
    examples = collocations = 0
    for path in sorted(ENTRIES.glob("*.json")):
        for entry in json.loads(path.read_text()):
            for example in entry.get("ex", []):
                if example.get("en"):
                    sources.add(example["en"].strip())
                    examples += 1
            for collocation in entry.get("col", []):
                en, _ = collocation_parts(collocation)
                if en:
                    sources.add(en)
                    collocations += 1
    SOURCES.write_text(json.dumps(sorted(sources), ensure_ascii=False))
    print(f"examples={examples} collocations={collocations} unique={len(sources)}")


def apply() -> None:
    try:
        from mishkal.tashkeel import TashkeelClass
    except ImportError:
        raise SystemExit("Mishkal is required. Install it with: pip install mishkal")

    source_list = json.loads(SOURCES.read_text())
    translations = json.loads(TRANSLATIONS.read_text())
    if len(source_list) != len(translations):
        raise SystemExit(f"translation count mismatch: {len(source_list)} != {len(translations)}")

    camel_lines: list[str] = []
    if VOCALIZED.exists():
        camel_lines = VOCALIZED.read_text().splitlines()
        if len(camel_lines) != len(translations):
            raise SystemExit(f"vocalized count mismatch: {len(camel_lines)} != {len(translations)}")

    tashkeel = TashkeelClass()
    arabic: dict[str, str] = {}
    unmarked = 0
    for index, (source, translated) in enumerate(zip(source_list, translations), 1):
        value = re.sub(r"\s+", " ", translated).strip()
        if camel_lines and camel_lines[index - 1].strip():
            value = camel_lines[index - 1].replace("\x01", " ").strip()
        if not ARABIC.search(value):
            raise SystemExit(f"non-Arabic translation at {index}: {source!r} -> {value!r}")
        if not DIACRITIC.search(value):
            try:
                vocalized = re.sub(r"\s+", " ", tashkeel.tashkeel(value).replace("\x01", " ")).strip()
                if ARABIC.search(vocalized):
                    value = vocalized
            except Exception:
                pass
        if not DIACRITIC.search(value):
            unmarked += 1
        arabic[source] = value

    examples = collocations = 0
    for path in sorted(ENTRIES.glob("*.json")):
        items = json.loads(path.read_text())
        for entry in items:
            for example in entry.get("ex", []):
                source = example.get("en", "").strip()
                value = arabic.get(source)
                if not value:
                    raise SystemExit(f"missing example translation: {source!r}")
                example["ar"] = value
                examples += 1
            updated = []
            for collocation in entry.get("col", []):
                en, zh = collocation_parts(collocation)
                value = arabic.get(en)
                if not value:
                    raise SystemExit(f"missing collocation translation: {en!r}")
                updated.append(f"{en}｜{zh}｜{value}")
                collocations += 1
            if updated:
                entry["col"] = updated
        path.write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")))
    print(f"examples={examples} collocations={collocations} unmarked={unmarked}")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"prepare", "apply"}:
        raise SystemExit("usage: arabic-examples.py prepare|apply")
    prepare() if sys.argv[1] == "prepare" else apply()


if __name__ == "__main__":
    main()
