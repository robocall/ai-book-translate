#!/usr/bin/env python3
"""
Split one big text file into paragraph-aware chunks for book_translate.py.

- Packs whole paragraphs until adding another would exceed --max-words.
- Never splits mid-paragraph; oversized paragraphs are split on sentence boundaries.
- Sentences longer than max become their own chunk (rare).
- For Chinese (CJK ideographs), each character counts as one “word” for --max-words;
  English and similar scripts still use whitespace-separated tokens.

Example:
  python chunk_book.py book_source/romeo_and_juliet.txt \\
    --out-dir book_source/chunks --prefix chunk --max-words 400

Then in book_translate.py set:
  SOURCE_DIR = Path("book_source/chunks")
  CHUNK_PREFIX = "chunk"
  START_SECTION / END_SECTION to match how many chunk_*.txt files you got.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _is_cjk_ideograph(ch: str) -> bool:
    """Rough detection of CJK unified / extension ideographs (classical/modern Chinese)."""
    if len(ch) != 1:
        return False
    o = ord(ch)
    return (
        0x3400 <= o <= 0x4DBF  # Extension A
        or 0x4E00 <= o <= 0x9FFF  # Unified
        or 0x20000 <= o <= 0x323AF  # Extensions B–H (rare chars)
    )


def word_count(text: str) -> int:
    """
    Size estimate for chunking. For text that contains CJK ideographs, each
    ideograph counts as 1 unit (Chinese is usually unspaced). Latin tokens are
    counted separately so mixed text still behaves reasonably.
    """
    cjk = sum(1 for c in text if _is_cjk_ideograph(c))
    if cjk:
        latin = len(
            re.findall(r"[A-Za-z0-9]+(?:['\-][A-Za-z0-9]+)?", text)
        )
        return cjk + latin
    return len(re.findall(r"\S+", text))


def split_paragraphs(text: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []
    parts = re.split(r"\n\s*\n+", text)
    return [p.strip() for p in parts if p.strip()]


def split_sentences(paragraph: str) -> list[str]:
    # Simple sentence split; good enough for chunking (not for NLP precision).
    if any(_is_cjk_ideograph(c) for c in paragraph):
        pieces = re.split(r"(?<=[。！？!?])\s*", paragraph.strip())
    else:
        pieces = re.split(r"(?<=[.!?])\s+", paragraph.strip())
    return [s.strip() for s in pieces if s.strip()]


def flatten_units(paragraphs: list[str], max_words: int) -> list[str]:
    """Turn paragraphs into units: whole para if small enough, else sentences."""
    units: list[str] = []
    for p in paragraphs:
        if word_count(p) <= max_words:
            units.append(p)
            continue
        for s in split_sentences(p):
            units.append(s)
    return units


def pack_chunks(units: list[str], max_words: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_w = 0

    for u in units:
        w = word_count(u)
        if w > max_words:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_w = 0
            chunks.append(u)
            continue

        if not current:
            current = [u]
            current_w = w
            continue

        if current_w + w <= max_words:
            current.append(u)
            current_w += w
        else:
            chunks.append("\n\n".join(current))
            current = [u]
            current_w = w

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def write_chunks(chunks: list[str], out_dir: Path, prefix: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i, body in enumerate(chunks, start=1):
        path = out_dir / f"{prefix}_{i:02d}.txt"
        path.write_text(body.strip() + "\n", encoding="utf-8")
        paths.append(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Split a book file into chunk_*.txt")
    parser.add_argument("input", type=Path, help="Path to one big .txt (or .md) file")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("book_source/chunks"),
        help="Directory for chunk_01.txt, … (default: book_source/chunks)",
    )
    parser.add_argument(
        "--prefix",
        default="chunk",
        help="Filename prefix (default: chunk → chunk_01.txt)",
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=400,
        help=(
            "Target max size per chunk: whitespace-words for Latin text; "
            "each CJK character counts as one unit for Chinese (default: 400)"
        ),
    )
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="Write out-dir/manifest.json with paths and word counts",
    )
    args = parser.parse_args()

    if args.max_words < 1:
        raise SystemExit("--max-words must be >= 1")

    path = args.input
    if not path.is_file():
        raise SystemExit(f"Input not found: {path}")

    raw = path.read_text(encoding="utf-8")
    paragraphs = split_paragraphs(raw)
    if not paragraphs:
        raise SystemExit("No non-empty paragraphs in input")

    units = flatten_units(paragraphs, args.max_words)
    chunks = pack_chunks(units, args.max_words)
    written = write_chunks(chunks, args.out_dir, args.prefix)

    print(f"Wrote {len(written)} files under {args.out_dir}/", file=sys.stderr)
    if args.manifest:
        manifest = [
            {
                "index": i,
                "file": str(p),
                "words": word_count(p.read_text(encoding="utf-8")),
            }
            for i, p in enumerate(written, start=1)
        ]
        (args.out_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
