"""Top-level CLI dispatcher.

Routes `utility-scripts-cli <group> <verb> [args...]` to the right command
module. Add a new verb by dropping a file in `commands/` and registering
it in COMMANDS. Add a new group by adding a parallel directory.
"""

from __future__ import annotations

import argparse
import sys
from typing import Callable, Dict

from utility_scripts_cli import __version__
from utility_scripts_cli.commands.slack_upload_file import main as slack_upload_file_main
from utility_scripts_cli.env import load_env

# group -> {verb -> (description, runner)}
# runner(argv_after_verb) -> exit code
COMMANDS: Dict[str, Dict[str, tuple[str, Callable[[list], int]]]] = {
    "slack": {
        "upload-file": (
            "Upload a file to a Slack channel or thread.",
            slack_upload_file_main,
        ),
        # Backcompat alias for the original verb. Same runner, same flags.
        "upload-image": (
            "Alias for upload-file (kept for backwards compatibility).",
            slack_upload_file_main,
        ),
    },
}


def _print_root_help() -> None:
    print("usage: utility-scripts-cli <group> <verb> [args...]", file=sys.stderr)
    print("", file=sys.stderr)
    print("groups:", file=sys.stderr)
    for group, verbs in COMMANDS.items():
        verb_list = ", ".join(verbs.keys())
        print(f"  {group}    verbs: {verb_list}", file=sys.stderr)
    print("", file=sys.stderr)
    print(f"version: {__version__}", file=sys.stderr)


def main(argv: list) -> int:
    load_env()
    if not argv or argv[0] in ("-h", "--help"):
        _print_root_help()
        return 0
    group = argv[0]
    if group not in COMMANDS:
        print(f"unknown group: {group}", file=sys.stderr)
        _print_root_help()
        return 2
    if len(argv) < 2:
        print(f"group '{group}' requires a verb", file=sys.stderr)
        _print_root_help()
        return 2
    verb = argv[1]
    if verb not in COMMANDS[group]:
        print(f"unknown verb: {group} {verb}", file=sys.stderr)
        print(f"known verbs for '{group}': {', '.join(COMMANDS[group].keys())}", file=sys.stderr)
        return 2
    _desc, runner = COMMANDS[group][verb]
    return runner(argv[2:])
