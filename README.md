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

`SLACK_BOT_TOKEN` is read from the environment, or from a profile-specific env file, or from the default XDG config file. Shell-exported values always win over files.

```bash
mkdir -p ~/.config/utility-scripts-cli
printf 'SLACK_BOT_TOKEN=xoxb-your-token\n' > ~/.config/utility-scripts-cli/.env
chmod 600 ~/.config/utility-scripts-cli/.env
```

You can also create the default file through the CLI:

```bash
utility-scripts-cli config init --token xoxb-your-token
```

For multiple agents or identities, create one profile file per token:

```bash
mkdir -p ~/.config/utility-scripts-cli/profiles
printf 'SLACK_BOT_TOKEN=xoxb-agent-a\n' > ~/.config/utility-scripts-cli/profiles/agent-a.env
printf 'SLACK_BOT_TOKEN=xoxb-agent-b\n' > ~/.config/utility-scripts-cli/profiles/agent-b.env
chmod 600 ~/.config/utility-scripts-cli/profiles/*.env
```

Or initialize profile files directly:

```bash
utility-scripts-cli --profile agent-a config init --token xoxb-agent-a
utility-scripts-cli --profile agent-b config init --token xoxb-agent-b
```

Then select a profile per invocation:

```bash
utility-scripts-cli --profile agent-a slack post-message --channel C0123 --text "hello"
utility-scripts-cli --profile agent-b slack upload-file --file /tmp/report.txt --channel C0123
```

Or set a default profile for a process/service:

```bash
export UTILITY_SCRIPTS_PROFILE=agent-a
utility-scripts-cli slack post-message --channel C0123 --text "hello"
```

Resolution order is:

1. Existing process environment variables, such as `SLACK_BOT_TOKEN`
2. Profile file from `--profile NAME` or `UTILITY_SCRIPTS_PROFILE`, loaded from `$XDG_CONFIG_HOME/utility-scripts-cli/profiles/NAME.env` or `~/.config/utility-scripts-cli/profiles/NAME.env`
3. Default file at `$XDG_CONFIG_HOME/utility-scripts-cli/.env` or `~/.config/utility-scripts-cli/.env`

`SLACK_API_URL` is optional — override the Slack API base URL (e.g. for the [`vercel-labs/emulate`](https://github.com/vercel-labs/emulate) local Slack emulator). You can also pass `--api-url` per invocation.

> The local emulator does not implement `files.getUploadURLExternal`, so emulator runs will fail at step 1 with a clear error from the server.

## Usage

```bash
utility-scripts-cli --help
utility-scripts-cli config init --help
utility-scripts-cli slack --help
utility-scripts-cli slack post-message --help
utility-scripts-cli slack upload-file --help
utility-scripts-cli slack upload-file --file /abs/shot.png --channel C0123 --caption "Latest"
```

For full flag lists, run `utility-scripts-cli slack post-message --help` or `utility-scripts-cli slack upload-file --help`. The legacy verb `slack upload-image` (with `--image`) is kept as a backwards-compatible alias.

## Requirements

- [`mise`](https://mise.jdx.dev/) — pinned Python toolchain + task runner (only needed when working inside a clone of this repo)
- A POSIX shell + `python3` (3.8+) + `curl` (only needed for the online installer)

## Local development (inside a clone)

If you're contributing to this repo, the dev tasks let you iterate on the CLI without re-installing:

```bash
mise install                  # provision the pinned Python
mise run install              # pip install -r requirements.txt (for in-repo runs)
mise run cli -- --help        # run the in-repo dispatcher
mise run cli -- config init --help
mise run cli-install          # run install.sh --yes locally (same as the online installer)
```

See `skills/` for agent-facing entry points (e.g. `slack-upload-file`).

## Layout

```
bin/utility-scripts-cli         Entry script (installed to ~/.local/share/utility-scripts-cli/lib/ by install.sh)
utility_scripts_cli/            Installable Python package
  cli.py                        Dispatcher (group → verb → command)
  env.py                        XDG-aware .env loader
  commands/                     One module per verb
    config_init.py              Create default/profile config files
    slack_post_message.py       Slack chat.postMessage helper
    slack_upload_file.py        Slack 2-step external upload
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
- `skills/slack-upload-file/SKILL.md` — the agent skill that drives the `slack upload-file` subcommand.
