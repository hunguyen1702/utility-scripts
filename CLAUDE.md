# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project intent

A collection of personal utility scripts for productivity and common workflows (e.g., sending files to Slack, taking actions on Notion, etc.). The repo produces a single installable CLI, `utility-scripts-cli`, written in **Python**. The project uses **mise** for toolchain/version management and ships a POSIX `sh` online installer.

## Toolchain

- **Language**: Python (version pinned via `mise`)
- **Version manager**: `mise` — use `mise` tasks / `mise.toml` rather than ad-hoc Python invocations
- Run `mise install` after cloning to provision the pinned toolchain

## Conventions for new commands

- One module per verb under `utility_scripts_cli/commands/<group>_<verb>.py`. Each module exposes a `main(argv: list) -> int` function. Register it in `COMMANDS` in `utility_scripts_cli/cli.py`.
- The CLI's argparse is the single user-facing parser for a verb — add a `--help` that documents the verb's flags.
- Configuration: read secrets from the environment first; then from a selected profile at `$XDG_CONFIG_HOME/utility-scripts-cli/profiles/<name>.env` (or `~/.config/utility-scripts-cli/profiles/<name>.env`) when `--profile` or `UTILITY_SCRIPTS_PROFILE` is set; finally fall back to `$XDG_CONFIG_HOME/utility-scripts-cli/.env` (or `~/.config/utility-scripts-cli/.env`). The loader is in `utility_scripts_cli/env.py` and is called once at the top of `cli.main()`. Do not re-load it inside a command.
- Pin new Python deps in `requirements.txt` (this repo does not use `pyproject.toml`).
- Never hard-code tokens — `.env` is git-ignored; commit `.env.example` instead.

## Commands

```bash
mise install                                          # provision pinned Python
mise run install                                      # pip install -r requirements.txt
mise run cli -- --help                                # run the in-repo dispatcher
mise run cli -- config init --help
mise run cli -- slack upload-file --file <p> --channel <id>
mise run cli-install                                  # run install.sh --yes locally
```

For installed users:

```bash
curl -fsSL https://raw.githubusercontent.com/hunguyen1702/utility-scripts/main/install.sh | sh -s -- --yes
utility-scripts-cli slack upload-file --file <path> --channel <id>
```

## Architecture

- `bin/utility-scripts-cli` — entry script invoked by the shim at `~/.local/bin/utility-scripts-cli`. Imports `utility_scripts_cli.cli.main`.
- `utility_scripts_cli/cli.py` — top-level dispatcher: parses `<group> <verb> [args...]` and routes to the right command module.
- `utility_scripts_cli/env.py` — XDG-aware `.env` loader for installed users.
- `utility_scripts_cli/commands/config_init.py` — Creates the default `.env` or a profile-specific config file.
- `utility_scripts_cli/commands/slack_post_message.py` — Slack `chat.postMessage` helper for plain text or Block Kit messages.
- `utility_scripts_cli/commands/slack_upload_file.py` — Slack 2-step external upload (file upload; the verb `upload-image` is a backcompat alias).
- `install.sh` — POSIX sh installer; downloads the package + `requirements.txt` from raw GitHub, creates a venv at `~/.local/share/utility-scripts-cli/venv`, and writes the shim at `~/.local/bin/utility-scripts-cli`.
  Keep its fetch/copy list aligned with `utility_scripts_cli/cli.py` imports. A missing command module in the installed layout can break startup before argument parsing, including `utility-scripts-cli --help`.
- `uninstall.sh` / `install.sh --uninstall` — remove the shim and the share dir.
- `mise.toml` — toolchain pin and task runner entrypoints.

Keep this section current when adding a new command or shared helper.

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

## Environment & debugging notes

- **Shim runs under `/bin/sh`** (GNU bash 3.2 on macOS), not the user's interactive shell. On macOS, `set -gx VAR val` in `fish` does not always propagate to `/bin/sh` subshells reliably — for secrets the XDG config files under `~/.config/utility-scripts-cli/` are the durable source, either the default `.env` or `profiles/<name>.env` for per-agent/per-identity setups.
- **Claude Code's Bash tool runs in an isolated shell**, separate from the user's fish/bash session. `echo $TOKEN` from the tool will be empty even if the user has it set. To verify env loading end-to-end, ask the user to run the command in their own shell, or write a token value into the XDG config file the CLI will read for that run, either the default `.env` or a selected `profiles/<name>.env`.
- **Two distinct error modes to tell apart when upload fails:**
  - `Error: SLACK_BOT_TOKEN env var is required.` → CLI never reached Slack; env loading failed.
  - `slack_sdk.errors.SlackApiError: ... 'error': 'invalid_auth'` → CLI reached Slack with a token but the token was rejected. Check token validity/scope, not env loading.
