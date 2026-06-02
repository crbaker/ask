# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```sh
# One-time setup
virtualenv venv && source venv/bin/activate
pip install -r requirements.txt

# Lint (the only static-check configured for the project)
pylint ask

# Run from source
python -m ask

# Build a standalone executable into ./dist/ask/ask
pyinstaller --clean -y -n ask ./ask/__main__.py
# or rebuild from the committed spec
pyinstaller --clean -y ask.spec
```

There is no test suite or test runner wired up in this repo.

### Required environment variables
- `ANTHROPIC_API_KEY` — needed for the default REPL flow (Claude backend).
- `CHATGPT_API_KEY` — needed only if switching the REPL back to the ChatGPT backend (see Architecture).
- `CLAUDE_MODEL` / `CHATGPT_MODEL` — optional overrides; defaults are `claude-3-haiku-20240307` and `gpt-5`.

## Architecture

`ask` is a single-command Typer CLI that drops the user into a REPL. `ask/__main__.py` is just the entry point — all behavior lives in `ask/conversation.py`, with persistence helpers in `ask/replay.py`.

### REPL dispatch (`conversation.start_repl`)
The loop reads a line, then routes it by **prefix match** (lowercased) before falling through to "treat as a model query":

| Prefix      | Handler                            | Notes |
|-------------|------------------------------------|-------|
| `exit`      | inline                             | quits |
| `cls`       | inline                             | clears screen and conversation buffer |
| `copy`      | `handle_copy`                      | `copy` → last response; `copy all` → whole conversation, joined with `\n` |
| `help`      | `handle_help`                      | prints the supported commands |
| `open`      | `handle_open` (see below)          | result becomes a user turn prefixed with `"Please read this text:"` |
| `del`       | `handle_delete` → `replay.delete_conversation` | requires a tag arg |
| `replay`    | `handle_replay`                    | no arg → list saved; with tag → replaces in-memory conversation |
| `save`      | `handle_save` → `replay.save_conversation` | requires a tag arg |
| anything else | sent to the model                | rejected if the input is a single word ("Query too short") |

The conversation buffer is a plain `list[dict]` of `{role, content}` messages, mutated in place; `cls` and `replay <tag>` are the only things that reset it.

### Model backends
Two functions exist: `ask_claude` (Anthropic SDK) and `ask_chatgpt` (OpenAI SDK). `start_repl` currently calls `ask_claude` in both the `open` branch and the default query branch. `fetch_model` returns the Claude model for the startup banner. To switch backends, both call sites and `fetch_model` must change together — there is no runtime toggle.

### `handle_open` content extraction
Dispatch is by URL scheme then file extension, in this order:
1. `http*` + YouTube host → `read_youtube` (uses `pytubefix`, prefers `en` captions, falls back to `a.en`; returns `None` if neither exists).
2. Other `http*` → `read_url` (requests + `html2text`, fixed `Mozilla/5.0` UA, 30s timeout).
3. `.txt` → `read_txt_file` (utf-8).
4. `.opus` → `read_opus_file`: shells out to `ffmpeg` to convert to `.wav` next to the source, then transcribes with `speech_recognition`'s Google recognizer, then deletes the wav. **`ffmpeg` must be on PATH for this branch.**
5. Anything else → `read_file`, which always tries `pypdf.PdfReader` regardless of extension.

All extractors swallow exceptions and return `None`; the REPL prints "No text found in the file" on `None`.

### Persistence
- `~/.ask_history` — readline history, capped at 100 entries, registered via `atexit`.
- `~/.ask_replay` — a single **pickle** dict mapping tag → conversation list. `replay.fetch_replay` / `_save_replay` are the only readers/writers; treat the file as opaque and never hand-edit. Because it's pickle, schema changes to conversation entries will silently break old replays.

### Packaging
`ask.spec` is the source of truth for PyInstaller builds (one-folder layout, console mode, UPX on). The plain `pyinstaller ./ask/__main__.py` command in the README regenerates an equivalent spec; prefer building from the committed `ask.spec` to keep the configuration stable.
