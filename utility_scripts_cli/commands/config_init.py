"""Initialize config files for utility-scripts-cli."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from utility_scripts_cli.env import config_dir

EPILOG = """\
examples:
  # Create the default config file
  utility-scripts-cli config init --token xoxb-xxx

  # Create a profile-specific config file
  utility-scripts-cli --profile agent-a config init --token xoxb-agent-a

  # Create a template without writing a real token yet
  utility-scripts-cli --profile agent-b config init

env vars:
  UTILITY_SCRIPTS_PROFILE   Select the target profile when --profile is omitted
"""


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="utility-scripts-cli config init",
        description="Create the default .env file or a profile-specific config file.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def _target_path() -> Path:
    profile = os.environ.get("UTILITY_SCRIPTS_PROFILE", "").strip()
    if profile:
        return config_dir() / "profiles" / f"{profile}.env"
    return config_dir() / ".env"


def _render_env(token: str | None, api_url: str | None) -> str:
    lines = []
    if token:
        lines.append(f"SLACK_BOT_TOKEN={token}")
    else:
        lines.append("SLACK_BOT_TOKEN=xoxb-your-token")
    if api_url:
        lines.append(f"SLACK_API_URL={api_url}")
    lines.append("")
    return "\n".join(lines)


def _write_file(path: Path, content: str, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        print(
            f"Error: config already exists at {path}. Re-run with --force to overwrite.",
            file=sys.stderr,
        )
        sys.exit(2)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o600)


def _do_init(args: argparse.Namespace) -> int:
    path = _target_path()
    content = _render_env(args.token, args.api_url)
    _write_file(path, content, args.force)
    print(f"Wrote config: {path}")
    if "xoxb-your-token" in content:
        print("Next: replace the placeholder SLACK_BOT_TOKEN with a real token.")
    return 0


def main(argv: list) -> int:
    parser = build_parser()
    parser.add_argument(
        "--token",
        default=None,
        help="Slack bot token to write. If omitted, write a placeholder template.",
    )
    parser.add_argument(
        "--api-url",
        default=None,
        help="Optional SLACK_API_URL to write into the config file.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the target config file if it already exists.",
    )
    args = parser.parse_args(argv)
    return _do_init(args)
