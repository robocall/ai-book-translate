# Long-text translation with Ollama

This CLI translates a long book/text into a different language or a different tone (e.g., Gen Z) using a local [Ollama](https://ollama.com/) model.

Feeding a long book into an LLM one paragraph at a time—with no memory of what came before—usually gives weak results. The model loses track of characters and plot, introducing inconsistencies. This repo helps by chunking the text to fit the context window and carrying a rolling summary forward so each translated chunk is aware of the story so far.

This repo consists of two small scripts packaged as a CLI:
- `chunk_book.py`: split one big text file into paragraph-aware chunks to fit into an LLM's limited context window
- `book_translate.py`: translate each chunk while maintaining a rolling “story so far” context for narrative consistency.

Sample results are committed under `book_output/old_dragonbeard_english/` and `book_output/the_monkeys_paw_genz/`.

## Contents

- [Prerequisites](#prerequisites)
- [Install](#install)
- [Quickstart: *Old Dragonbeard* (Chinese → English)](#quickstart-old-dragonbeard-chinese--english)
  - [1) Chunk a long text file](#1-chunk-a-long-text-file)
  - [2) Translate the chunks](#2-translate-the-chunks)
  - [3) Sample output](#3-sample-output)
- [Example: *The Monkey's Paw* (English → Gen Z tone)](#example-the-monkeys-paw-english--gen-z-tone)
  - [1) Chunk the story](#1-chunk-the-story)
  - [2) Run `translate-chunks` with a Gen Z voice](#2-run-translate-chunks-with-a-gen-z-voice)
  - [3) Sample output](#3-sample-output-1)
- [Example: Resume a partial translation](#example-resume-a-partial-translation)
- [CLI reference](#cli-reference)
  - [`chunk-book` (from `chunk_book.py`)](#chunk-book-from-chunk_bookpy)
  - [`translate-chunks` (from `book_translate.py`)](#translate-chunks-from-book_translatepy)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Prerequisites

- Python `>= 3.10`
- Ollama running locally (we assume the Ollama API URL: `http://localhost:11434`)
- A model pulled in Ollama (default: `gemma3:4b`)

## Install

From this folder:

```bash
pip install -e .
```

This uses the CLI entry points defined in `pyproject.toml`.

## Quickstart: *Old Dragonbeard* (Chinese → English)

This walkthrough chunks the classical Chinese tale *Old Dragonbeard*（虬髯客傳）and translates the resulting chunks into English. The source text is included under `book_source/`.

### 1) Chunk a long text file

```bash
chunk-book book_source/old_dragonbeard_original_chinese.txt --out-dir book_source/old_dragonbeard_chunks --prefix chunk --max-words 280 --manifest
```

Output chunks will be written to the directory [`book_source/old_dragonbeard_chunks/`](book_source/old_dragonbeard_chunks/)

### 2) Translate the chunks

```bash
translate-chunks \
  --book-title "Old Dragonbeard" \
  --source-dir book_source/old_dragonbeard_chunks \
  --output-dir book_output/old_dragonbeard_english \
  --start-section 1 \
  --target-language English
```

The translated output will be written to `--output-dir` as:
- `chunk_XX.md`: the translated, condensed recap for chunk `XX`
- `chunk_XX.context.md`: updated “story so far” after chunk `XX`
- `story_so_far.md`: rolling “story so far”
- `index.json`: metadata listing the generated chunk files and word count

### 3) Sample output

For convenience, an excerpt of the translated result is shown below. The full translation can be found in this repo at ([`book_output/old_dragonbeard_english`](book_output/old_dragonbeard_english)).

**Chunk 1**
> Emperor Yang of the Sui, seeking stability, appointed Sima Yang as governor of Chang’an, a position that reflected the emperor’s increasing reliance on Sima’s influence amidst widespread political turmoil. Sima’s behavior was marked by arrogance and extravagance, deviating from traditional protocols for court officials. He habitually sat on his bed when receiving audiences, displaying lavish gifts and employing numerous servants, a practice considered inappropriate for a high-ranking official. This trend intensified as the reign neared its end.
>
> During this period, Li Jing, a county magistrate dressed as a commoner, presented the emperor with a strategic proposal...

**Last chunk (8 of 8)** 
> Following the Emperor’s confirmed identity and Li Jing’s return to Chang’an, discussions centered on the origins of Zhang’s strategic thinking. It was suggested that Zhang’s military methods owed a significant debt to the teachings of Wei Gong. This observation highlighted a key element of Zhang’s approach – a pragmatic, adaptable strategy rooted in established military principles, rather than a purely ambitious or heroic one. The encounter underscored the calculated nature of Zhang’s actions, revealing a response to political instability rather than a pursuit of conquest.

Other options:
- `--target-language` lets you translate output into a language different from the source.
- `--voice` is a tone/style label used in the prompt. The default is "clear, neutral prose." Other options include "easier reading level", "slang", or "Gen Z." 
- The translator maintains continuity via `story_so_far.md` in the output folder.

## Example: *The Monkey's Paw* (English → Gen Z tone)

The short story **“The Monkey’s Paw”** (W. W. Jacobs) is included as `book_source/the_monkeys_paw.txt` (public domain text from [Project Gutenberg #12122](https://www.gutenberg.org/ebooks/12122)). Here the source and target language are both English; the model rewrites each chunk in a Gen Z–style voice instead of translating from another language.

### 1) Chunk the story

```bash
chunk-book book_source/the_monkeys_paw.txt --out-dir book_source/the_monkeys_paw_chunks --prefix chunk --max-words 400 --manifest
```
Output chunks will be written to the directory [`book_source/the_monkeys_paw_chunks/`](book_source/the_monkeys_paw_chunks/).

### 2) Run `translate-chunks` with a Gen Z voice

```bash
translate-chunks \
  --book-title "The Monkey's Paw" \
  --chunk-prefix chunk \
  --source-dir book_source/the_monkeys_paw_chunks \
  --output-dir book_output/the_monkeys_paw_genz \
  --start-section 1 \
  --target-language English \
  --voice "Gen Z: casual, internet-native, witty but still clear; not cringe, not a lecture"
```
You can find outputs in [`book_output/the_monkeys_paw_genz/`](book_output/the_monkeys_paw_genz/).

### 3) Sample output
For convenience, an excerpt of the translated result is shown below. The full translation can be found in this repo at ([`book_output/the_monkeys_paw_genz`](book_output/the_monkeys_paw_genz)).

**Chunk 1**:

> Okay, so the Whites are chilling in their ridiculously isolated villa, playing chess with a seriously intense dad and a slightly cooler son. The grandma’s knitting, the wind’s howling, and Mr. White is already stressing about how awful their location is – basically, it’s a swampy nightmare. 

**Last chunk (11 of 11)**:

> Okay, so things are *seriously* spiraling. Mr. White’s on the floor, basically having a full-blown panic, desperately searching for the monkey’s paw before whatever creepy dude outside gets in. The knocking is insane – like, a constant barrage – and his wife’s just casually dropping a chair against the door. You can hear the bolt slowly backing out, and then *boom*, he finds the paw and throws out his last wish. The knocking just…stops. The wind rushes in, his wife lets out this massive wail of disappointment, and he sprints to her side, then bolts for the gate. The streetlamp’s flickering, and the road’s deserted. It’s pure chaos.

## Example: Resume a partial translation

If only some chunks of the translation are completed and you want to complete it later:
- Set `--start-section` to the next chunk number
- Optionally, omit `--end-section` to auto-detect the last chunk number from `--source-dir`.
- Leave the same `--output-dir` (so `story_so_far.md` is loaded automatically)

An example command for the Monkey's Paw to translate only chunks 8-11 would be:
```bash
translate-chunks \
  --book-title "The Monkey's Paw" \
  --chunk-prefix chunk \
  --source-dir book_source/the_monkeys_paw_chunks \
  --output-dir book_output/the_monkeys_paw_genz \
  --start-section 8 \
  --end-section 11 \
  --target-language English \
  --voice "Gen Z: casual, internet-native, witty but still clear; not cringe, not a lecture"
```

## CLI reference

### `chunk-book` (from `chunk_book.py`)

```bash
chunk-book INPUT_FILE --out-dir OUT_DIR --prefix PREFIX --max-words 400 --manifest
```

| Option | Required? | Type | Default | Meaning |
|--------|-------------|------|---------|---------|
| `INPUT_FILE` | **Required** | path | No default, required field. | Source `.txt` or `.md` file to split |
| `--out-dir` | Optional | path | `book_source/chunks` | Directory for `PREFIX_01.txt`, `PREFIX_02.txt`, … |
| `--prefix` | Optional | string | `chunk` | Filename prefix |
| `--max-words` | Optional | int | `400` | Target max size per chunk; CJK counts one character per unit |
| `--manifest` | Optional | bool | false | If set, also write `manifest.json` in `--out-dir`: a JSON array of `{ "index", "file", "words" }` per chunk (1-based chunk number, path to the chunk file, word count) |

### `translate-chunks` (from `book_translate.py`)

```bash
translate-chunks \
  --book-title "..." \
  --chunk-prefix chunk \
  --source-dir path/to/chunks \
  --output-dir path/to/output \
  --start-section 1 \
  --end-section N \
  --target-language English \
  --voice "clear, neutral prose"
```

| Option | Required? | Type | Default | Meaning |
|--------|-------------|------|---------|---------|
| `--book-title` | Optional | string | `Old Dragonbeard (虬髯客傳)` | Title passed into the prompt; helps the model with context |
| `--chunk-prefix` | Optional | string | `chunk` | Must match source filenames (`{prefix}_01.txt`, …) |
| `--source-dir` | Optional | path | `book_source/old_dragonbeard_chunks` | Folder containing chunk files |
| `--output-dir` | Optional | path | `book_output/old_dragonbeard_english` | Where to write `chunk_XX.md`, `story_so_far.md`, etc. |
| `--start-section` | Optional | int | `1` | First chunk index to translate (use for resume) |
| `--end-section` | Optional | int | null | Last chunk index; when omitted, the script will infer the highest chunk number from files in `--source-dir` |
| `--target-language` | Optional | string | `English` | Language for model output. This will be injected into the LLM prompt, so the flag takes freeform text |
| `--voice` | Optional | string | `clear, neutral prose` | Style/tone label for the recap. This will be injected into the LLM prompt, so the flag takes freeform text |

All `translate-chunks` flags are optional; omitting path flags uses the defaults above. Model name and generation temperature are not CLI flags.

Output files in `OUTPUT_DIR`:
- `chunk_XX.md`: the translated, condensed recap for that chunk
- `chunk_XX.context.md`: the updated rolling “story so far” after the chunk (for debugging)
- `story_so_far.md`: the latest “story so far”, used to give the LLM story context
- `index.json`: metadata listing generated chunk files


## Troubleshooting

| Error | Solutions |
|--------------|------------------------|
| `error: externally-managed-environment` when running `pip install` | Create a virtual environment and install there: `python3 -m venv .venv`, then `source .venv/bin/activate` (macOS/Linux) or `.venv\Scripts\activate` (Windows), then `pip install -e .`. Run `chunk-book` / `translate-chunks` with that same environment’s Python. |
| `ModuleNotFoundError: No module named 'ollama'` | The interpreter you use to run the script does not have dependencies installed. Use the venv above, or `python3 -m pip install ollama` into the environment you actually use. |
| `Connection refused` / `Failed to connect` to Ollama | Start the Ollama app or run `ollama serve`. Ensure nothing else is blocking `http://127.0.0.1:11434`. |
| Model error such as `model ... not found` | Pull the default model: `ollama pull gemma3:4b`, or change the default model tag in the translator module to one you already have (`ollama list`). |
| `No non-empty paragraphs in input` (`chunk-book`) | The file is empty or has no paragraph breaks. Add content, or separate paragraphs with a blank line. |
| `Input not found` (`chunk-book`) | Fix the path to your source file (run from the repo root or use an absolute path). |
| `Could not infer end-section: no chunk files found` (`translate-chunks`) | Point `--source-dir` at the folder that contains `chunk_01.txt` (or `.md`), and make sure `--chunk-prefix` matches the filenames (e.g. `chunk` for `chunk_01.txt`). |
| `Missing source for chunk N` / `FileNotFoundError` for a chunk | `--end-section` is larger than the number of chunks, or files are missing / misnumbered. Re-run `chunk-book` or set `--end-section` to the last existing chunk index. |
| `Warning: no <<<CONTEXT>>> block for section N` | The model did not follow the required output format; the script fills in a fallback. Retry the run, switch to a stronger model, or lower the generation temperature in the translator module if needed. |
| Output reads like a loose summary, wrong names, or drift across chunks | Note that the pipeline is tuned for **compressed recap**, not literal translation. Consider modifying the prompt, or increasing the number of words per chunk. Please also open an issue with your example in this github repo.|

## License

This package is licensed under the MIT license. Note that any source texts you translate may have their own licenses.

