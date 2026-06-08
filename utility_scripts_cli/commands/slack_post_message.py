"""Post a message (plain text or Block Kit) to a Slack channel or thread.

The blocks input is a JSON file (`--blocks-file`) whose top level is a list
of Block Kit block objects. Designed so the JSON can be drafted in the
Block Kit Builder (https://app.slack.com/tools/block-kit-builder) and
saved as-is.

`--text` is required when `--blocks-file` is set, per Slack's guidance:
without a fallback `text` the message still posts, but mobile
notifications show "No preview available" and the workspace may surface
a warning. We enforce it client-side to fail fast.

`--channel` must be a resolved Slack ID (`C…` for channels, `D…` for DMs,
`G…` for shared channels). User IDs (`U…`) are not accepted by
`chat.postMessage`. Resolve a DM with `conversations.open(users=...)`
first if needed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

EPILOG = """\
examples:
  # Plain text
  utility-scripts-cli slack post-message --channel C0123 --text "Hello from CLI"

  # Block Kit from a JSON file (design in Block Kit Builder, save the JSON)
  utility-scripts-cli slack post-message --channel C0123 \\
      --text "Build status update" --blocks-file build-status.json

  # Reply inside a thread
  utility-scripts-cli slack post-message --channel C0123 \\
      --text "follow-up" --thread-ts 1717000000.000200

env vars:
  SLACK_BOT_TOKEN   Bot user OAuth token (required, needs chat:write scope)
  SLACK_API_URL     Override Slack API base URL (e.g. http://localhost:4003/api for the emulator)
"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="utility-scripts-cli slack post-message",
        description="Post a plain-text or Block Kit message to a Slack channel or thread.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--channel", required=True, help="Channel ID (C…/D…/G…); user IDs are not accepted")
    p.add_argument(
        "--text",
        default=None,
        help=(
            "Message text. Required when --blocks-file is set (Slack uses it as "
            "the notification fallback and accessibility text)."
        ),
    )
    p.add_argument(
        "--blocks-file",
        default=None,
        help="Path to a JSON file containing a list of Block Kit block objects",
    )
    p.add_argument("--thread-ts", default=None, help="Reply into a thread with this parent ts")
    p.add_argument(
        "--api-url",
        default=None,
        help="Override SLACK_API_URL for this run (advanced; usually not needed)",
    )
    return p


def _resolve_token() -> str:
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print("Error: SLACK_BOT_TOKEN env var is required.", file=sys.stderr)
        sys.exit(2)
    return token


def _build_client(token: str, api_url_override: str | None) -> WebClient:
    api_url = api_url_override or os.environ.get("SLACK_API_URL")
    if api_url:
        base = api_url if api_url.endswith("/") else api_url + "/"
        return WebClient(token=token, base_url=base)
    return WebClient(token=token)


def _load_blocks(path_arg: str) -> list[dict[str, Any]]:
    path = os.path.abspath(path_arg)
    if not os.path.isfile(path):
        print(f"Error: --blocks-file not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        data = Path(path).read_text(encoding="utf-8")
    except OSError as e:
        print(f"Error: could not read --blocks-file {path}: {e}", file=sys.stderr)
        sys.exit(2)
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        print(f"Error: --blocks-file is not valid JSON: {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(parsed, list):
        print("Error: --blocks-file must contain a JSON array of block objects.", file=sys.stderr)
        sys.exit(2)
    if not parsed:
        print("Error: --blocks-file must not be empty.", file=sys.stderr)
        sys.exit(2)
    for i, block in enumerate(parsed):
        if not isinstance(block, dict) or not isinstance(block.get("type"), str):
            print(
                f"Error: --blocks-file blocks[{i}] must be an object with a 'type' field.",
                file=sys.stderr,
            )
            sys.exit(2)
    return parsed


def _do_post_message(args: argparse.Namespace) -> int:
    blocks: list[dict[str, Any]] | None = None
    if args.blocks_file:
        blocks = _load_blocks(args.blocks_file)
        if not args.text:
            print(
                "Error: --text is required when --blocks-file is set (Slack uses it as a fallback).",
                file=sys.stderr,
            )
            sys.exit(2)
    elif not args.text:
        print("Error: --text is required (or pass --blocks-file to send a Block Kit message).", file=sys.stderr)
        sys.exit(2)

    token = _resolve_token()
    client = _build_client(token, args.api_url)

    kwargs: dict[str, Any] = {"channel": args.channel, "text": args.text}
    if blocks is not None:
        kwargs["blocks"] = blocks
    if args.thread_ts is not None:
        kwargs["thread_ts"] = args.thread_ts

    try:
        resp = client.chat_postMessage(**kwargs)
    except SlackApiError as e:
        err = e.response.get("error", str(e))
        print(f"Error: chat.postMessage failed: {err}", file=sys.stderr)
        sys.exit(1)

    ts = (resp.data or {}).get("ts", "(no ts)")
    channel = (resp.data or {}).get("channel", args.channel)
    print(f"Posted ts={ts} to {channel}")
    return 0


def main(argv: list) -> int:
    """Dispatcher entrypoint. argv is the args after the verb."""
    args = build_parser().parse_args(argv)
    return _do_post_message(args)
