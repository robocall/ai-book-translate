#!/usr/bin/env python3
"""
Translate Dante's Inferno canto by canto with Ollama.

Install:
  pip install ollama

Run:
  python inferno_translate.py
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
from typing import Any

import ollama


MODEL = "gemma3:4b"
START_CANTO = 1
END_CANTO = 3 #inclusive
OUTPUT_DIR = Path("inferno_genz_output")
SOURCE_DIR = Path("inferno_source")


def load_canto_text(canto_number: int) -> str:
    candidates = [
        SOURCE_DIR / f"canto_{canto_number:02d}.txt",
        SOURCE_DIR / f"canto_{canto_number:02d}.md",
    ]
    for path in candidates:
        if path.exists():
            return path.read_text(encoding="utf-8")
    raise FileNotFoundError(
        f"Missing source text for canto {canto_number}. "
        f"Expected one of: {', '.join(str(p) for p in candidates)}"
    )


def build_prompt(canto_number: int, canto_text: str) -> str:
    return f"""You are a literary translator.
Task: Translate Dante's Inferno Canto {canto_number} into natural Gen Z English.

Rules:
- Output ONLY the translated canto text.
- Do NOT add commentary, notes, headings, analysis, or explanations.
- Keep all major content from the source; do not summarize or omit sections.
- Preserve stanza/line breaks where possible.
- If a line is unclear, still provide your best faithful translation.

SOURCE CANTO TEXT (translate everything between tags):
<CANTO>
{canto_text}
</CANTO>"""


def translate_canto(canto_number: int, canto_text: str, model: str = MODEL) -> str:
    prompt = build_prompt(canto_number, canto_text)
    response = ollama.generate(
        model=model,
        prompt=prompt,
        stream=False,
        options={"temperature": 0.2, "num_predict": 4096},
    )
    return response["response"]


def save_canto(output_dir: Path, canto_number: int, text: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"canto_{canto_number:02d}.md"
    path.write_text(text.strip() + "\n", encoding="utf-8")


def main() -> int:
    results: list[dict[str, Any]] = []
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for canto_number in range(START_CANTO, END_CANTO + 1):
        print(f"Translating canto {canto_number}...", file=sys.stderr)
        canto_text = load_canto_text(canto_number)
        translated = translate_canto(canto_number, canto_text)
        save_canto(OUTPUT_DIR, canto_number, translated)
        results.append(
            {
                "canto": canto_number,
                "model": MODEL,
                "output_file": str(OUTPUT_DIR / f"canto_{canto_number:02d}.md"),
            }
        )

    index_path = OUTPUT_DIR / "index.json"
    index_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(results)} canto translations to {OUTPUT_DIR}/", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
