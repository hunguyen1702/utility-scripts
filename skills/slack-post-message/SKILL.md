---
name: slack-post-message
description: Send a Slack message with the installed `utility-scripts-cli` tool, especially when the user wants a formatted Block Kit message posted to a channel or an existing thread. Use this skill whenever the user wants to post structured Slack content such as status cards, alerts, deployment summaries, rich sections, action-heavy updates, or "formatted Slack blocks", "Block Kit", "post this to Slack", "send this message to thread", or "reply in Slack with blocks". Do NOT use this skill for file uploads, channel management, search, or other Slack operations.
---

# slack-post-message

Send a plain-text or Block Kit Slack message by invoking `utility-scripts-cli slack post-message`. This skill is primarily for formatted Block Kit payloads, but it also covers simple text messages and thread replies through the same subcommand.

## When to use

Use this skill when the user wants to:

- Post a formatted Block Kit message to a Slack channel
- Reply inside an existing Slack thread
- Send a plain-text Slack message through the repo's installed CLI
- Reuse a Block Kit Builder JSON payload and post it directly

Do not use it for file uploads or any non-message Slack workflow.

## Required inputs

Before running, confirm you have:

| Input                         | Required | Notes                                                                                                                                       |
| ----------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Channel**                   | Yes      | Slack channel ID (`C…`, `D…`, `G…`). Names like `#general` and user IDs (`U…`) must be resolved first.                                     |
| **Text** (`--text`)           | Usually  | Required for plain-text messages, and also required whenever `--blocks-file` is used as the fallback/accessibility text.                   |
| **Blocks file**               | For Block Kit | Absolute path to a JSON file whose top level is a non-empty array of Block Kit block objects.                                           |
| **Thread ts** (`--thread-ts`) | No       | Parent message timestamp for a thread reply. Format: `<seconds>.<microseconds>`, e.g. `1717000000.000200`.                                |
| **API URL** (`--api-url`)     | No       | Only when intentionally targeting a non-production Slack API or emulator.                                                                   |

If the user asks for a Block Kit message but has not provided the JSON yet, draft the payload first, save it to a file, then run the CLI with `--blocks-file`.

## Block Kit expectations

`--blocks-file` must point to a UTF-8 JSON file whose top level is a list of block objects exactly as exported from Slack Block Kit Builder.

- The file must exist and contain valid JSON.
- The top level must be a non-empty JSON array.
- Each element must be an object with a string `type` field.
- `--text` is still required when using blocks so Slack has notification fallback and accessibility text.

The simplest workflow is:

1. Draft the layout in Block Kit Builder.
2. Save the JSON payload as-is.
3. Provide a concise human-readable fallback string with `--text`.
4. Post it with `utility-scripts-cli slack post-message`.

## Resolving channels

`chat.postMessage` requires a resolved Slack conversation ID.

- **`#name` or channel name**: resolve it to a `C…` or `G…` ID before calling the CLI.
- **DM with a user (`U…`)**: open the DM first with `conversations.open(users=...)` and use the resulting `D…` channel ID.

Do not pass a raw user ID to `--channel`. The command rejects user IDs by design.

## How to run

Plain text:

```bash
utility-scripts-cli slack post-message --channel C0123 --text "Hello from CLI"
```

Block Kit:

```bash
utility-scripts-cli slack post-message \
  --channel C0123 \
  --text "Build status update" \
  --blocks-file /abs/path/to/build-status.json
```

Reply in a thread:

```bash
utility-scripts-cli slack post-message \
  --channel C0123 \
  --text "follow-up" \
  --thread-ts 1717000000.000200
```

Block Kit in a thread:

```bash
utility-scripts-cli slack post-message \
  --channel C0123 \
  --text "Deployment summary" \
  --blocks-file /abs/path/to/deploy-summary.json \
  --thread-ts 1717000000.000200
```

For `--help` and the full flag list:

```bash
utility-scripts-cli slack post-message --help
```

## If the CLI is not installed

This skill assumes `utility-scripts-cli` is already installed and on `PATH` (typically `~/.local/bin/utility-scripts-cli`).

Do not run the installer from this skill. If `command -v utility-scripts-cli` is empty, tell the user the CLI is missing and point them to the repo install instructions:

- https://github.com/hunguyen1702/utility-scripts#online-install-recommended

## Configuration

The CLI reads `SLACK_BOT_TOKEN` and `SLACK_API_URL` from the environment, or from `$XDG_CONFIG_HOME/utility-scripts-cli/.env` (falling back to `~/.config/utility-scripts-cli/.env`). Shell-exported values always win over the file.

One-time setup after install:

```bash
mkdir -p ~/.config/utility-scripts-cli
printf 'SLACK_BOT_TOKEN=xoxb-your-token\n' > ~/.config/utility-scripts-cli/.env
chmod 600 ~/.config/utility-scripts-cli/.env
```

## Debugging

Common failures:

- `Error: SLACK_BOT_TOKEN env var is required.`: env loading failed before any Slack call.
- `Error: --text is required when --blocks-file is set ...`: the command intentionally refuses Block Kit posts without fallback text.
- `Error: --blocks-file is not valid JSON ...`: the payload file is malformed.
- `Error: chat.postMessage failed: channel_not_found`: `--channel` is not a valid resolved conversation ID.

When drafting blocks, prefer short fallback text that still makes sense in notifications, screen readers, and thread previews.
