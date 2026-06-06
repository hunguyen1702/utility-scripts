# utility-scripts

A small collection of personal CLI utilities for common workflows (sending files to Slack, talking to Notion, etc.). The tool is installed as a single binary, `utility-scripts-cli`, with subcommands per workflow.

## Online install (recommended)

macOS / Linux, no sudo required. Installs to `~/.local`:

```bash
curl -fsSL https://raw.githubusercontent.com/hunguyen1702/utility-scripts/main/install.sh | sh -s -- --yes
```

This places:

- `~/.local/bin/utility-scripts-cli` — the shim (on `PATH` for most macOS/Linux setups)
- `~/.local/share/utility-scripts-cli/lib/` — the CLI source
- `~/.local/share/utility-scripts-cli/venv/` — a hermetic Python venv with `slack-sdk` and `python-dotenv`

Re-run the same command to upgrade. To uninstall:

```bash
curl -fsSL https://raw.githubusercontent.com/hunguyen1702/utility-scripts/main/install.sh | sh -s -- --uninstall
```

> The installer does not touch your system Python. It only writes under `~/.local/`.

## Configuration

`SLACK_BOT_TOKEN` is read from the environment, or from `$XDG_CONFIG_HOME/utility-scripts-cli/.env` (falling back to `~/.config/utility-scripts-cli/.env`). Shell-exported values always win over the file.

```bash
mkdir -p ~/.config/utility-scripts-cli
printf 'SLACK_BOT_TOKEN=xoxb-your-token\n' > ~/.config/utility-scripts-cli/.env
chmod 600 ~/.config/utility-scripts-cli/.env
```

`SLACK_API_URL` is optional — override the Slack API base URL (e.g. for the [`vercel-labs/emulate`](https://github.com/vercel-labs/emulate) local Slack emulator). You can also pass `--api-url` per invocation.

> The local emulator does not implement `files.getUploadURLExternal`, so emulator runs will fail at step 1 with a clear error from the server.

## Usage

```bash
utility-scripts-cli --help
utility-scripts-cli slack --help
utility-scripts-cli slack upload-image --help
utility-scripts-cli slack upload-image --image /abs/shot.png --channel C0123 --caption "Latest"
```

For full flag list, run `utility-scripts-cli slack upload-image --help`.

## Requirements

- [`mise`](https://mise.jdx.dev/) — pinned Python toolchain + task runner (only needed when working inside a clone of this repo)
- A POSIX shell + `python3` (3.8+) + `curl` (only needed for the online installer)

## Local development (inside a clone)

If you're contributing to this repo, the dev tasks let you iterate on the CLI without re-installing:

```bash
mise install                  # provision the pinned Python
mise run install              # pip install -r requirements.txt (for in-repo runs)
mise run cli -- --help        # run the in-repo dispatcher
mise run cli-install          # run install.sh --yes locally (same as the online installer)
```

See `skills/` for agent-facing entry points (e.g. `slack-upload-image`).

## Layout

```
bin/utility-scripts-cli         Entry script (installed to ~/.local/share/utility-scripts-cli/lib/ by install.sh)
utility_scripts_cli/            Installable Python package
  cli.py                        Dispatcher (group → verb → command)
  env.py                        XDG-aware .env loader
  commands/                     One module per verb
    slack_upload_image.py       Slack 2-step external upload
install.sh                      POSIX sh online installer (curl|sh-friendly)
uninstall.sh                    POSIX sh uninstaller
mise.toml                       Toolchain pin + task runner entrypoints
requirements.txt                Python deps
.env.example                    Template for local secrets (do not commit .env)
CLAUDE.md                       Agent-facing project notes
skills/                         Agent-facing skill definitions
```

## See also

- `CLAUDE.md` — agent-facing project notes and the Slack upload gotchas (silent-failure modes: `POST` vs `PUT`, `channel_id` must be a resolved channel/user/DM ID, etc.).
- `skills/slack-upload-image/SKILL.md` — the agent skill that drives the `slack upload-image` subcommand.
