#!/usr/bin/env python3
"""Vocalize translated Arabic lines with CAMeL morphology and a Mishkal fallback."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

for package_dir in (Path("/private/tmp/camel-lib"), Path("/private/tmp/mishkal-lib")):
    if package_dir.exists():
        sys.path.insert(0, str(package_dir))

from camel_tools.disambig.mle import MLEDisambiguator  # noqa: E402
from camel_tools.tokenizers.word import simple_word_tokenize  # noqa: E402
from mishkal.tashkeel import TashkeelClass  # noqa: E402

TRANSLATIONS = Path("/private/tmp/arabic-example-translations.json")
OUTPUT = Path("/private/tmp/arabic-example-vocalized.txt")
DIACRITIC = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
MARKS = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed\u0640]")
WHITESPACE = re.compile(r"\s+|\S+")


def skeleton(value: str) -> str:
    return MARKS.sub("", value).replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")


def camel_vocalize(
    text: str, disambiguator: MLEDisambiguator, fallback: TashkeelClass
) -> str:
    output: list[str] = []
    for token in WHITESPACE.findall(text):
        if not token.strip():
            output.append(token)
            continue
        pieces = simple_word_tokenize(token)
        analyses = disambiguator.disambiguate(pieces)
        for item in analyses:
            candidates = [analysis.analysis.get("diac", item.word) for analysis in item.analyses]
            match = next((candidate for candidate in candidates if skeleton(candidate) == skeleton(item.word)), None)
            if match:
                output.append(match)
            else:
                try:
                    output.append(fallback.tashkeel(item.word).replace("\x01", " "))
                except Exception:
                    output.append(item.word)
    return "".join(output).replace("\x01", " ").strip()


def main() -> None:
    translations = json.loads(TRANSLATIONS.read_text())
    disambiguator = MLEDisambiguator.pretrained("calima-msa-r13")
    fallback = TashkeelClass()
    lines: list[str] = []
    for index, translated in enumerate(translations, 1):
        source = re.sub(r"\s+", " ", translated).strip()
        try:
            value = camel_vocalize(source, disambiguator, fallback)
        except Exception:
            value = ""
        if not DIACRITIC.search(value):
            try:
                value = fallback.tashkeel(source).replace("\x01", " ").strip()
            except Exception:
                value = source
        lines.append(re.sub(r"\s+", " ", value))
        if index % 500 == 0 or index == len(translations):
            print(f"vocalized {index}/{len(translations)}", flush=True)
    OUTPUT.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
