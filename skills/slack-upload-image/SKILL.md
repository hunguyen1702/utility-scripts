---
name: slack-upload-image
description: Upload an image to a Slack channel or thread using the repo's `slack_upload_image.py` script. Use this skill whenever the user wants to send, post, share, or attach an image/file to Slack — including screenshots, charts, photos, design mocks, logs, or any other image asset. Triggers on phrases like "upload this to Slack", "send to #channel", "post this screenshot to Slack", "share in thread", "slack it", or when the user provides an image path and a channel name/ID. Do NOT use this skill to send plain text messages, manage channels, or perform other Slack operations — only image/file upload via the 2-step external upload flow.
---

# slack-upload-image

Upload an image to a Slack channel or thread by invoking the `slack_upload_image.py` script in this repo. The script implements Slack's modern 2-step external upload flow (`files.getUploadURLExternal` → `POST` bytes → `files.completeUploadExternal`).

## When to use

Use this skill when the user wants to:
- Upload an image to a Slack channel
- Reply with an image inside an existing thread
- Share a screenshot, chart, mock, log, or any other image asset to Slack

Do not use it for plain text messages, channel management, search, or any non-upload Slack operation.

## Required inputs

Before running, confirm you have:

| Input | Required | Notes |
| --- | --- | --- |
| **Image path** | Yes | Absolute path to the file on disk. Reject obviously bad paths (non-existent, directory) before invoking. |
| **Channel** | Yes | Slack channel ID (`C…`, `D…`, `G…`). If the user gave a name like `#general` or a user ID (`U…`), resolve it first — see "Resolving channels" below. |
| **Caption** (`--caption`) | No | Initial comment posted with the file. |
| **Thread ts** (`--thread-ts`) | No | Parent message timestamp to reply in-thread. Format: `<seconds>.<microseconds>`, e.g. `1717000000.000200`. |
| **Title** (`--title`) | No | Display name in Slack. Defaults to the filename. |

If anything required is missing, ask the user — do not guess.

## Resolving channels

The `channel_id` argument to `files.completeUploadExternal` must be a resolved Slack ID, not a name or a user ID. Two common cases:

- **`#name` or channel name**: resolve via `conversations.list` (filter by name) or use the existing channel cache. If you can't resolve, ask the user for the ID.
- **DM with a user (`U…`)**: DMs require the DM channel ID (`D…`). Open the IM first with `conversations.open(users=…)` to get the `D…` ID, then pass that to the script.

Do not pass `U…` IDs directly — the upload will succeed but the file won't be shared (silent failure, see [[slack-gotchas]]).

## How to run

The script is `slack_upload_image.py` at the repo root. The project uses `mise` for toolchain/version management, so prefer:

```bash
mise run slack-upload-image -- --image /abs/path/to/shot.png --channel C0123 --caption "Latest deploy"
```

Or, equivalently:

```bash
python slack_upload_image.py --image /abs/path/to/shot.png --channel C0123 --caption "Latest deploy"
```

Always run from the repo root so `import env` picks up `.env` (where `SLACK_BOT_TOKEN` lives). The script loads `.env` automatically, but shell-exported `SLACK_BOT_TOKEN` wins.

For `--help` and full flag list, run `mise run slack-upload-image -- --help`.

## Optional: pointing at a local Slack emulator

The script accepts `--api-url` (or `SLACK_API_URL` env var) to target a non-production Slack API. The local emulator from the `vercel-labs/emulate` skill does not implement `files.getUploadURLExternal`, so emulator runs will fail at step 1 with a clear server error — that's expected, not a bug in your call.

## After the run

The script prints a permalink on success. Surface that to the user so they can click through to the uploaded message.

## Debugging

If the upload fails or the file uploads but doesn't appear in the channel, read [[slack-gotchas]] before debugging — the most common causes are silent and the script's `ok: true` response can be misleading.
