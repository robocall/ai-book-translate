#!/usr/bin/env python3
"""
Translate numbered book chunks with Ollama.

Each prompt includes a short summary of everything that happened in prior chunks.
Output is a condensed recap in your chosen voice (default: clear, neutral prose), shorter than the source chunk.

Put source text in SOURCE_DIR as {CHUNK_PREFIX}_01.txt, _02.txt, … (or .md).
Outputs go to OUTPUT_DIR as {CHUNK_PREFIX}_01.md, …

Install:
  pip install ollama

Run:
  python book_translate.py

Resume later (e.g. chunks 4–10): set START_SECTION = 4 and ensure
OUTPUT_DIR / story_so_far.md exists (written after each chunk in prior runs).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import ollama

# --- per-book knobs ---
BOOK_TITLE = "Old Dragonbeard (虬髯客傳)"
SECTION_LABEL = "Chunk"
CHUNK_PREFIX = "chunk"

MODEL = "gemma3:4b"
START_SECTION = 1
END_SECTION = 8  # inclusive; for resume set START_SECTION to next chunk (load story_so_far.md)

SOURCE_DIR = Path("book_source/old_dragonbeard_chunks")
OUTPUT_DIR = Path("book_output/old_dragonbeard_english")

# Canonical rolling summary for the *next* chunk (and for resuming another day).
STORY_SO_FAR_FILE = OUTPUT_DIR / "story_so_far.md"

# How long the rolling “story so far” should stay (soft cap in the prompt).
MAX_PRIOR_CONTEXT_WORDS = 350
# Compression: summary retelling, not a parallel rewrite.
CHUNK_SUMMARY_GUIDANCE = (
    "Treat this as a tight recap in the requested voice, not a line-by-line or paragraph-by-paragraph "
    "translation. Merge ideas: fewer sentences and paragraphs than the source. "
    "Rough length: about 25–40% of the source word count on long chunks; on short chunks, "
    "still compress (e.g. one or two short paragraphs) instead of matching the source’s shape. "
    "Keep the important beats, turns of thought, and mood — drop repetition and fine-grained detail."
)

DEFAULT_TARGET_LANGUAGE = "English"
# “Voice” is a prompt label; it defines the style of the generated text.
DEFAULT_VOICE = "clear, neutral prose"


def load_section_text(section_number: int) -> str:
    stem = f"{CHUNK_PREFIX}_{section_number:02d}"
    candidates = [
        SOURCE_DIR / f"{stem}.txt",
        SOURCE_DIR / f"{stem}.md",
    ]
    for path in candidates:
        if path.exists():
            return path.read_text(encoding="utf-8")
    raise FileNotFoundError(
        f"Missing source for {SECTION_LABEL.lower()} {section_number}. "
        f"Expected one of: {', '.join(str(p) for p in candidates)}"
    )


def build_prompt(
    section_number: int,
    source_text: str,
    prior_context: str,
    target_language: str,
    voice: str,
) -> str:
    prior_block = prior_context.strip() if prior_context.strip() else "(No prior sections yet — this is the start of the book.)"
    return f"""You are adapting literature for a {voice} voice in {target_language}.

Book: {BOOK_TITLE}
Current part: {SECTION_LABEL} {section_number}

STORY SO FAR (everything that happened in earlier {SECTION_LABEL.lower()}s — use only for continuity, do not repeat it verbatim):
{prior_block}

Keep “story so far” mentally under ~{MAX_PRIOR_CONTEXT_WORDS} words when you write the updated context below.

SOURCE FOR THIS SECTION ONLY:
<SOURCE>
{source_text}
</SOURCE>

Tasks:
1) Summarize THIS section in a {voice} voice in {target_language}: flowing recap, not a structural mirror of the source.
   {CHUNK_SUMMARY_GUIDANCE}
   Match the requested voice; stay readable. No lecture, no “as we can see”, no study guide tone.
   Do NOT align one output paragraph per original paragraph; collapse and paraphrase across the whole section.
2) Update STORY SO FAR: one concise block that merges prior context with what happens in this section, so the next prompt has full continuity. That block should be neutral narrative summary (who did what, mood, key facts), in {target_language}, not your {voice} pastiche.

Hard rules:
- Do NOT add commentary outside the two blocks below.
- Do NOT paste the full source into the context block — summarize.
- In <<<GENZ>>>, do NOT preserve the source’s paragraph breaks on purpose; use whatever short shape fits the recap.
- Do NOT start <<<GENZ>>> with throat-clearing openers like “Okay, so” or “Alright, so” — begin directly with the recap.

Output EXACTLY in this shape (including the marker lines):

<<<GENZ>>>
[Translation / recap of this section only — compressed, not parallel to the source layout]
<<<CONTEXT>>>
[Updated story-so-far for all sections through this one, including this section]
"""


def parse_translation_and_context(raw: str) -> tuple[str, str | None]:
    text = raw.strip()
    if "<<<GENZ>>>" not in text:
        return text, None
    after_genz = text.split("<<<GENZ>>>", 1)[1]
    if "<<<CONTEXT>>>" in after_genz:
        genz_part, ctx_part = after_genz.split("<<<CONTEXT>>>", 1)
        return genz_part.strip(), ctx_part.strip()
    return after_genz.strip(), None


def translate_section(
    section_number: int,
    source_text: str,
    prior_context: str,
    target_language: str,
    voice: str,
    model: str = MODEL,
) -> tuple[str, str]:
    prompt = build_prompt(
        section_number,
        source_text,
        prior_context,
        target_language=target_language,
        voice=voice,
    )
    response = ollama.generate(
        model=model,
        prompt=prompt,
        stream=False,
        options={"temperature": 0.35, "num_predict": 6144},
    )
    raw = response["response"]
    genz, new_ctx = parse_translation_and_context(raw)
    if new_ctx is None:
        print(
            f"Warning: no <<<CONTEXT>>> block for section {section_number}; "
            "extending story context with a short fallback.",
            file=sys.stderr,
        )
        snippet = " ".join(genz.split())[:400]
        new_ctx = (prior_context.strip() + f"\n\n[Section {section_number}]: " + snippet).strip()
    return genz, new_ctx


def save_section(output_dir: Path, section_number: int, text: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{CHUNK_PREFIX}_{section_number:02d}"
    path = output_dir / f"{stem}.md"
    path.write_text(text.strip() + "\n", encoding="utf-8")


def save_context_sidecar(output_dir: Path, section_number: int, context: str) -> None:
    stem = f"{CHUNK_PREFIX}_{section_number:02d}"
    path = output_dir / f"{stem}.context.md"
    path.write_text(context.strip() + "\n", encoding="utf-8")


def save_story_so_far(path: Path, context: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(context.strip() + "\n", encoding="utf-8")


def load_story_so_far_for_resume(output_dir: Path, start_section: int) -> str:
    """Load cumulative context so chunk N can see story through chunk N-1."""
    if start_section <= 1:
        return ""

    state_path = output_dir / "story_so_far.md"
    if state_path.exists():
        return state_path.read_text(encoding="utf-8").strip()

    prev = start_section - 1
    stem = f"{CHUNK_PREFIX}_{prev:02d}"
    fallback = output_dir / f"{stem}.context.md"
    if fallback.exists():
        print(
            f"Loaded story context from {fallback.name} (no {state_path.name} yet).",
            file=sys.stderr,
        )
        return fallback.read_text(encoding="utf-8").strip()

    print(
        f"Warning: no {state_path.name} or {stem}.context.md — "
        f"starting chunk {start_section} with empty prior context.",
        file=sys.stderr,
    )
    return ""


def main() -> int:
    # Must be declared before any argparse default values referencing these names.
    global BOOK_TITLE, SECTION_LABEL, CHUNK_PREFIX, SOURCE_DIR, OUTPUT_DIR, START_SECTION, END_SECTION, STORY_SO_FAR_FILE
    parser = argparse.ArgumentParser(
        description="Translate book chunks with rolling story context."
    )
    parser.add_argument(
        "--target-language",
        default=DEFAULT_TARGET_LANGUAGE,
        help="Language for the output (e.g. English). Model will translate the source into this language.",
    )
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help='Voice/tone label for the generated text (default: "clear, neutral prose").',
    )
    parser.add_argument(
        "--book-title",
        default=BOOK_TITLE,
        help="Book title to include in the prompt.",
    )
    parser.add_argument(
        "--section-label",
        default=SECTION_LABEL,
        help="Label for each chunk/section in the prompt (e.g. Chunk, Scene, Act Scene).",
    )
    parser.add_argument(
        "--chunk-prefix",
        default=CHUNK_PREFIX,
        help="Chunk filename prefix to read: {prefix}_01.txt, etc.",
    )
    parser.add_argument(
        "--source-dir",
        default=str(SOURCE_DIR),
        help="Directory containing chunk files.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory to write translated chunk files.",
    )
    parser.add_argument(
        "--start-section",
        type=int,
        default=START_SECTION,
        help="First chunk number to translate.",
    )
    parser.add_argument(
        "--end-section",
        type=int,
        default=None,
        help="Last chunk number to translate (default: infer from existing chunks).",
    )
    args = parser.parse_args()

    # Override module-level defaults from CLI.
    BOOK_TITLE = args.book_title
    SECTION_LABEL = args.section_label
    CHUNK_PREFIX = args.chunk_prefix
    SOURCE_DIR = Path(args.source_dir)
    OUTPUT_DIR = Path(args.output_dir)
    START_SECTION = args.start_section
    END_SECTION = args.end_section if args.end_section is not None else END_SECTION
    STORY_SO_FAR_FILE = OUTPUT_DIR / "story_so_far.md"

    if args.end_section is None:
        # Infer max chunk number by scanning chunk files in SOURCE_DIR.
        import re as _re

        best = None
        for p in SOURCE_DIR.glob(f"{CHUNK_PREFIX}_*.txt"):
            m = _re.match(rf"^{_re.escape(CHUNK_PREFIX)}_(\d+)\.txt$", p.name)
            if m:
                best = int(m.group(1)) if best is None else max(best, int(m.group(1)))
        for p in SOURCE_DIR.glob(f"{CHUNK_PREFIX}_*.md"):
            m = _re.match(rf"^{_re.escape(CHUNK_PREFIX)}_(\d+)\.md$", p.name)
            if m:
                best = int(m.group(1)) if best is None else max(best, int(m.group(1)))
        if best is not None:
            END_SECTION = best
        else:
            raise SystemExit(
                f"Could not infer end-section: no chunk files found in {SOURCE_DIR}/"
            )

    results: list[dict[str, Any]] = []
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    running_context = load_story_so_far_for_resume(OUTPUT_DIR, START_SECTION)

    target_language = args.target_language
    voice = args.voice

    for section_number in range(START_SECTION, END_SECTION + 1):
        print(
            f"Translating {SECTION_LABEL.lower()} {section_number}...", file=sys.stderr
        )
        source_text = load_section_text(section_number)
        genz, running_context = translate_section(
            section_number,
            source_text,
            running_context,
            target_language=target_language,
            voice=voice,
        )
        save_section(OUTPUT_DIR, section_number, genz)
        save_context_sidecar(OUTPUT_DIR, section_number, running_context)
        save_story_so_far(STORY_SO_FAR_FILE, running_context)
        stem = f"{CHUNK_PREFIX}_{section_number:02d}"
        results.append(
            {
                "section": section_number,
                "model": MODEL,
                "output_file": str(OUTPUT_DIR / f"{stem}.md"),
                "context_file": str(OUTPUT_DIR / f"{stem}.context.md"),
                "story_so_far_file": str(STORY_SO_FAR_FILE),
            }
        )

    index_path = OUTPUT_DIR / "index.json"
    index_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(results)} translations to {OUTPUT_DIR}/", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
