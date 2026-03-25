# Long-text translation with Ollama

Tools for translating a long book/text into a different language or a different tone (e.g., Gen Z) using a local [Ollama](https://ollama.com/) model.

This repo consists of two small scripts packaged as a CLI:
- `chunk_book.py`: split one big text file into paragraph-aware chunks to fit into an LLM's limited context window
- `book_translate.py`: translate each chunk while maintaining a rolling “story so far” context for narrative consistency.

Sample runs (same settings as the quickstart examples below) are committed under `book_output/old_dragonbeard_english/` and `book_output/the_monkeys_paw_genz/` so you can read outputs without running Ollama.

## Prerequisites

- Python `>= 3.10`
- Ollama running locally (we assume the Ollama API URL: `http://localhost:11434`)
- A model pulled in Ollama (default in `book_translate.py`: `gemma3:4b`)

## Install

From this folder:

```bash
pip install -e .
```

This uses the CLI entry points defined in `pyproject.toml`.

## Quickstart
This quickstart example chunks the classical Chinese tale *Old Dragonbeard*（《虬髯客傳）and then translates the resulting chunks into English. The source text is included under `book_source/`.

### 1) Chunk a big text file

```bash
chunk-book book_source/old_dragonbeard_original_chinese.txt --out-dir book_source/old_dragonbeard_chunks --prefix chunk --max-words 280 --manifest
```

This will output:
- `book_source/old_dragonbeard_chunks/chunk_01.txt`, `chunk_02.txt`, ...
- optional `manifest.json` with chunk word counts

### 2) Translate the chunks

```bash
translate-chunks \
  --book-title "Old Dragonbeard (虬髯客傳)" \
  --section-label "Chunk" \
  --chunk-prefix chunk \
  --source-dir book_source/old_dragonbeard_chunks \
  --output-dir book_output/old_dragonbeard_english \
  --start-section 1 \
  --end-section 8 \
  --target-language English
```

(Default `--voice` is clear, neutral prose; add `--voice "..."` only if you want a different tone.)

The translated output will be written to `--output-dir` as:
- `chunk_XX.md`: the translated, condensed recap for chunk `XX`
- `chunk_XX.context.md`: updated “story so far” after chunk `XX`
- `story_so_far.md`: rolling “story so far”
- `index.json`: metadata listing the generated chunk files and word count


Notes:
- `--target-language` lets you translate output into a language different from the source.
- `--voice` is a tone/style label used in the prompt. The default is **clear, neutral prose** (not slang or Gen Z unless you set it).
- The translator maintains continuity via `story_so_far.md` in the output folder.

## Example: *The Monkey's Paw* (English → Gen Z tone)

The short story **“The Monkey’s Paw”** (W. W. Jacobs) is included as `book_source/the_monkeys_paw.txt` (public domain text from [Project Gutenberg #12122](https://www.gutenberg.org/ebooks/12122)). Here the **source and target language are both English**; the model **rewrites** each chunk in a Gen Z–style voice instead of translating from another language.

### 1) Chunk the story

```bash
chunk-book book_source/the_monkeys_paw.txt --out-dir book_source/the_monkeys_paw_chunks --prefix chunk --max-words 400 --manifest
```

With the copy in this repo, that yields **11** chunks (`chunk_01.txt` … `chunk_11.txt`).

### 2) Run `translate-chunks` with a Gen Z `--voice`

```bash
translate-chunks \
  --book-title "The Monkey's Paw" \
  --section-label "Chunk" \
  --chunk-prefix chunk \
  --source-dir book_source/the_monkeys_paw_chunks \
  --output-dir book_output/the_monkeys_paw_genz \
  --start-section 1 \
  --end-section 11 \
  --target-language English \
  --voice "Gen Z: casual, internet-native, witty but still clear; not cringe, not a lecture"
```

Outputs match the quickstart layout (`chunk_XX.md`, `chunk_XX.context.md`, `story_so_far.md`, `index.json`), but the recap is phrased in the voice you asked for. Omit `--end-section` to auto-detect the last chunk number from `--source-dir`.

## CLI reference

### `chunk-book` (from `chunk_book.py`)

```bash
chunk-book INPUT_FILE --out-dir OUT_DIR --prefix PREFIX --max-words 400 --manifest
```

Options:
- `--out-dir`: output directory for `PREFIX_01.txt`, `PREFIX_02.txt`, ...
- `--prefix`: filename prefix
- `--max-words`: target max words per chunk (splits by paragraph; oversized paragraphs split by sentence boundaries)
- `--manifest`: also write `manifest.json`

### `translate-chunks` (from `book_translate.py`)

```bash
translate-chunks \
  --book-title "..." \
  --section-label "Chunk" \
  --chunk-prefix chunk \
  --source-dir path/to/chunks \
  --output-dir path/to/output \
  --start-section 1 \
  --end-section N \
  --target-language English \
  --voice "clear, neutral prose"
```

Output files in `OUTPUT_DIR`:
- `chunk_XX.md`: the translated, condensed recap for that chunk
- `chunk_XX.context.md`: the updated rolling “story so far” after the chunk (debug/backup)
- `story_so_far.md`: the latest “story so far” (for resume)
- `index.json`: metadata listing generated chunk files

## Resume support

If you stop and want to continue later:
- set `--start-section` to the next chunk number
- leave the same `--output-dir` (so `story_so_far.md` is loaded automatically)

## Troubleshooting

| What you see | What usually fixes it |
|--------------|------------------------|
| `error: externally-managed-environment` when running `pip install` | Create a virtual environment and install there: `python3 -m venv .venv`, then `source .venv/bin/activate` (macOS/Linux) or `.venv\Scripts\activate` (Windows), then `pip install -e .`. Run `chunk-book` / `translate-chunks` with that same environment’s Python. |
| `ModuleNotFoundError: No module named 'ollama'` | The interpreter you use to run the script does not have dependencies installed. Use the venv above, or `python3 -m pip install ollama` into the environment you actually use. |
| `Connection refused` / `Failed to connect` to Ollama | Start the Ollama app or run `ollama serve`. Ensure nothing else is blocking `http://127.0.0.1:11434`. |
| Model error such as `model ... not found` | Pull the default model: `ollama pull gemma3:4b`, or edit `MODEL` in `book_translate.py` to a tag you already have (`ollama list`). |
| `No non-empty paragraphs in input` (`chunk-book`) | The file is empty or has no paragraph breaks. Add content, or separate paragraphs with a blank line. |
| `Input not found` (`chunk-book`) | Fix the path to your source file (run from the repo root or use an absolute path). |
| `Could not infer end-section: no chunk files found` (`translate-chunks`) | Point `--source-dir` at the folder that contains `chunk_01.txt` (or `.md`), and make sure `--chunk-prefix` matches the filenames (e.g. `chunk` for `chunk_01.txt`). |
| `Missing source for chunk N` / `FileNotFoundError` for a chunk | `--end-section` is larger than the number of chunks, or files are missing / misnumbered. Re-run `chunk-book` or set `--end-section` to the last existing chunk index. |
| `Warning: no <<<CONTEXT>>> block for section N` | The model did not follow the required output format; the script fills in a fallback. Retry the run, switch to a stronger model, or lower temperature in `book_translate.py` if needed. |
| Output reads like a loose summary, wrong names, or drift across chunks | The pipeline is tuned for **compressed recap**, not literal translation. For faithful English, prefer a dedicated translation workflow or a larger model; keep rolling context in `story_so_far.md` for continuity. |

## License

This package is licensed under the MIT license. Note that any source texts you translate may have their own licenses.

