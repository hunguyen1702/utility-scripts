# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project intent

A collection of personal utility scripts for productivity and common workflows (e.g., sending files to Slack, taking actions on Notion, etc.). Scripts are written in **Python** and the project uses **mise** for toolchain/version management.

## Toolchain

- **Language**: Python (version pinned via `mise`)
- **Version manager**: `mise` — use `mise` tasks / `.mise.toml` rather than ad-hoc Python invocations
- Run `mise install` after cloning to provision the pinned toolchain

## Conventions for new scripts

- One script per workflow at the repo root (or a short subdirectory). Each script must support `--help`.
- Register a `mise` task in `mise.toml` so it runs via `mise run <name>` as well as `python <script>.py`.
- Load secrets from `.env` by adding `import env  # noqa: F401` at the top of the script. `env.py` is the shared loader; shell-exported vars win over `.env`.
- Pin new Python deps in `requirements.txt` (this repo does not use `pyproject.toml`).
- Never hard-code tokens — `.env` is git-ignored; commit `.env.example` instead.

## Commands

```bash
mise install                                          # provision pinned Python
mise run install                                      # pip install -r requirements.txt
mise run slack-upload-image -- --image <path> --channel <id>   # see script --help
```

## Architecture

- `env.py` — shared `.env` loader; every script imports it as `import env  # noqa: F401`.
- `slack_upload_image.py` — uploads an image to a Slack channel or DM via the 2-step external upload flow.
- `mise.toml` — toolchain pin and task runner entrypoints.

Keep this section current when adding a new script or shared helper.

## Documentation resources

Before implementing anything that talks to the Slack platform, do not assume parameter names, method names, or field names from memory or from a plan. Verify against the official sources:

- Start at https://docs.slack.dev/llms.txt to locate the relevant method.
- Then open the method's reference page at `https://docs.slack.dev/reference/methods/<method_name>` to confirm exact field names. For example, `files.completeUploadExternal` takes `channel_id` (not `channel`) — getting this wrong uploads the file successfully but never share it to a channel, and the failure is silent.
- For the Python SDK (`slack-sdk`), verify the local signature before calling. Method names on `WebClient` are camelCase, e.g. `files_completeUploadExternal` (not `files_complete_upload_external`). Inspect with either:

  ```python
  import inspect
  from slack_sdk.web.client import WebClient
  print(inspect.getsource(WebClient.files_completeUploadExternal))
  # or
  help(WebClient.files_completeUploadExternal)
  ```

The 30-second cost of a lookup is much lower than the cost of debugging a silently-misnamed field or method.

### Slack upload gotchas (silent failures)

Both of these return `ok: true` but leave the file unshared (`channels: []`, `ims: []`). Always log the full `completeUploadExternal` response while developing.

- **Step 2 uses POST, not PUT.** The `upload_url` from `files.getUploadURLExternal` requires `POST` with the file bytes. `PUT` is accepted (HTTP 200) but the bytes are never parsed — `mimetype`/`filetype` come back empty and step 3 silently skips sharing.
- **`channel_id` must be a resolved channel ID** (`C…`, `D…`, `G…`). User IDs (`U…`) are not auto-resolved by `files.completeUploadExternal` even though `chat.postMessage` accepts them. For DMs, resolve with `conversations.open(users=...)` first.
