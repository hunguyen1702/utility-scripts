# utility-scripts

A small collection of personal Python utilities for common workflows (sending files to Slack, talking to Notion, etc.). Each script is standalone, has a `--help`, and is wired up as a [`mise`](https://mise.jdx.dev/) task.

## Requirements

- [`mise`](https://mise.jdx.dev/) — pinned Python toolchain + task runner
- The Python deps listed in `requirements.txt` (installed via `mise run install`)

## Getting started

```bash
mise install                # provision the pinned Python (see .mise.toml / mise.toml)
mise run install            # pip install -r requirements.txt
cp .env.example .env        # then fill in real values
```

Secrets are loaded by importing `env` at the top of each script:

```python
import env  # noqa: F401
```

`env.py` reads `.env` from the project root; shell-exported vars take precedence, which is handy for one-off overrides.

> Never commit `.env`. Commit `.env.example` as the template.

## Scripts

### `slack_upload_image.py`

Uploads an image to a Slack channel (or thread) via the modern 2-step external upload flow (`files.getUploadURLExternal` → POST bytes → `files.completeUploadExternal`).

```bash
# Post to a channel
python slack_upload_image.py --image shot.png --channel C0123 --caption "Latest"

# Reply in a thread
python slack_upload_image.py --image shot.png --channel C0123 --thread-ts 1717000000.000200
```

Or via the registered `mise` task:

```bash
mise run slack-upload-image -- --image shot.png --channel C0123
```

Run `python slack_upload_image.py --help` for the full flag list.

**Required env:** `SLACK_BOT_TOKEN` (needs the `files:write` scope).
**Optional env:** `SLACK_API_URL` — override the Slack API base URL (e.g. for the [`vercel-labs/emulate`](https://github.com/vercel-labs/emulate) local Slack emulator). You can also pass `--api-url`.

> The local emulator does not implement `files.getUploadURLExternal`, so emulator runs will fail at step 1 with a clear error from the server.

See the Slack upload gotchas in `CLAUDE.md` for silent-failure modes to watch for (`POST` vs `PUT`, `channel_id` must be a resolved channel/user/DM ID, etc.).

## Adding a new script

The project conventions are short — follow them and a new script drops in cleanly:

1. Add the script at the repo root (or a short subdirectory) and make sure it supports `--help`.
2. Register a `mise` task in `mise.toml` so it runs via `mise run <name>` as well as `python <script>.py`.
3. Load secrets with `import env  # noqa: F401` at the top of the script.
4. Pin any new Python deps in `requirements.txt` (this repo does not use `pyproject.toml`).
5. Never hard-code tokens — `.env` is git-ignored; commit `.env.example` instead.

## Layout

```
env.py                  Shared .env loader (imported by every script)
slack_upload_image.py   Slack image uploader
mise.toml               Toolchain pin + task runner entrypoints
requirements.txt        Python deps
.env.example            Template for local secrets (do not commit .env)
CLAUDE.md               Agent-facing project notes
```
