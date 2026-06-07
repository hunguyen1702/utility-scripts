---
name: slack-upload-file
description: Upload a file (image, PDF, log, CSV, ZIP, design mock, screenshot, or anything else) to a Slack channel or thread using the installed `utility-scripts-cli` tool. Use this skill whenever the user wants to send, post, share, attach, or upload a file/image to Slack — including screenshots, charts, photos, design mocks, logs, reports, archives. Triggers on phrases like "upload this to Slack", "send this PDF to #channel", "post this screenshot to Slack", "share this file in thread", "slack it", "send the log to Slack", or when the user provides a file path and a channel name/ID. Do NOT use this skill to send plain text messages, manage channels, search messages, or perform other Slack operations — only file upload via the 2-step external upload flow.
---

# slack-upload-file

Upload any file to a Slack channel or thread by invoking `utility-scripts-cli slack upload-file`. The CLI implements Slack's modern 2-step external upload flow (`files.getUploadURLExternal` → `POST` bytes → `files.completeUploadExternal`) and is content-type agnostic — images, PDFs, logs, archives, and arbitrary binary all go through the same path.

> Legacy: the verb `slack upload-image` and the flag `--image` are kept as aliases for backwards compatibility. New work should use `upload-file` / `--file`.

## When to use

Use this skill when the user wants to:
- Upload a file (image, PDF, log, CSV, ZIP, …) to a Slack channel
- Reply with a file inside an existing thread
- Share a screenshot, chart, mock, report, or any other asset to Slack

Do not use it for plain text messages, channel management, search, or any non-upload Slack operation.

## Required inputs

Before running, confirm you have:

| Input | Required | Notes |
| --- | --- | --- |
| **File path** | Yes | Absolute path to the file on disk. Reject obviously bad paths (non-existent, directory) before invoking. |
| **Channel** | Yes | Slack channel ID (`C…`, `D…`, `G…`). If the user gave a name like `#general` or a user ID (`U…`), resolve it first — see "Resolving channels" below. |
| **Caption** (`--caption`) | No | Initial comment posted with the file. |
| **Thread ts** (`--thread-ts`) | No | Parent message timestamp to reply in-thread. Format: `<seconds>.<microseconds>`, e.g. `1717000000.000200`. |
| **Title** (`--title`) | No | Display name in Slack. Defaults to the filename. |

If anything required is missing, ask the user — do not guess.

## Resolving channels

The `channel_id` argument to `files.completeUploadExternal` must be a resolved Slack ID, not a name or a user ID. Two common cases:

- **`#name` or channel name**: resolve via `conversations.list` (filter by name) or use the existing channel cache. If you can't resolve, ask the user for the ID.
- **DM with a user (`U…`)**: DMs require the DM channel ID (`D…`). Open the IM first with `conversations.open(users=…)` to get the `D…` ID, then pass that to the CLI.

Do not pass `U…` IDs directly — the upload will succeed but the file won't be shared (silent failure, see [[slack-gotchas]]).

## How to run

```bash
utility-scripts-cli slack upload-file --file /abs/path/to/report.pdf --channel C0123 --caption "Q2 report"
```

Images work the same way:

```bash
utility-scripts-cli slack upload-file --file /abs/path/to/shot.png --channel C0123 --caption "Latest deploy"
```

For `--help` and the full flag list:

```bash
utility-scripts-cli slack upload-file --help
```

### Auto-install fallback

If `utility-scripts-cli` is not on PATH (fresh machine, brand new shell session), install it before running:

```bash
if ! command -v utility-scripts-cli >/dev/null 2>&1; then
  curl -fsSL https://raw.githubusercontent.com/hunguyen1702/utility-scripts/main/install.sh | sh -s -- --yes
fi
utility-scripts-cli slack upload-file --file /abs/path/to/file.pdf --channel C0123
```

The installer places the binary in `~/.local/bin/utility-scripts-cli` (already on `PATH` on most macOS/Linux setups). It downloads a small set of files from GitHub, creates a hermetic venv at `~/.local/share/utility-scripts-cli/venv`, and installs the deps from `requirements.txt`. It does not touch system Python or any other file on the machine.

## Configuration

The CLI reads `SLACK_BOT_TOKEN` and `SLACK_API_URL` from the environment, or from `$XDG_CONFIG_HOME/utility-scripts-cli/.env` (falling back to `~/.config/utility-scripts-cli/.env`). Shell-exported values always win over the file.

One-time setup after install:

```bash
mkdir -p ~/.config/utility-scripts-cli
printf 'SLACK_BOT_TOKEN=xoxb-your-token\n' > ~/.config/utility-scripts-cli/.env
chmod 600 ~/.config/utility-scripts-cli/.env
```

## Optional: pointing at a local Slack emulator

The CLI accepts `--api-url` (or `SLACK_API_URL` env var) to target a non-production Slack API. The local emulator from the `vercel-labs/emulate` skill does not implement `files.getUploadURLExternal`, so emulator runs will fail at step 1 with a clear server error — that's expected, not a bug in your call.

## After the run

The CLI prints a permalink on success. Surface that to the user so they can click through to the uploaded message.

## Debugging

If the upload fails or the file uploads but doesn't appear in the channel, read [[slack-gotchas]] before debugging — the most common causes are silent and the script's `ok: true` response can be misleading.
