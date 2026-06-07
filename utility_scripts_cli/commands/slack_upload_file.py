"""Upload a file to a Slack channel or thread.

Implements Slack's modern 2-step external upload flow. Works against real
Slack by default; set SLACK_API_URL (or pass --api-url) to point at a
local Slack emulator such as the one from the vercel-labs/emulate skill.
The local emulator does not implement files.getUploadURLExternal, so
emulator runs will fail at step 1 with a clear server error.

The upload flow is content-type agnostic: images, PDFs, logs, CSVs, and
any other file types all go through the same path. The legacy --image
flag is kept as a hidden alias for --file so older callers keep working.
"""

from __future__ import annotations

import argparse
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

EPILOG = """\
examples:
  # Post a file to a channel
  utility-scripts-cli slack upload-file --file report.pdf --channel C0123 --caption "Q2 report"

  # Post an image (any file type works the same way)
  utility-scripts-cli slack upload-file --file shot.png --channel C0123 --caption "Latest"

  # Reply in a thread
  utility-scripts-cli slack upload-file --file shot.png --channel C0123 --thread-ts 1717000000.000200

env vars:
  SLACK_BOT_TOKEN   Bot user OAuth token (required, needs files:write scope)
  SLACK_API_URL     Override Slack API base URL (e.g. http://localhost:4003/api for the emulator)
"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="utility-scripts-cli slack upload-file",
        description="Upload a file (image, PDF, log, …) to a Slack channel or thread reply.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--file", dest="file", default=None, help="Path to the file to upload")
    # Backcompat alias for the original upload-image verb. Hidden from --help
    # so the documented surface is just --file, but old scripts/skills keep working.
    p.add_argument("--image", dest="image", default=None, help=argparse.SUPPRESS)
    p.add_argument("--channel", required=True, help="Channel ID (C…) or name (#… or name)")
    p.add_argument("--thread-ts", default=None, help="Reply into a thread with this parent ts")
    p.add_argument("--caption", default=None, help="Initial comment posted alongside the file")
    p.add_argument("--title", default=None, help="Title shown in Slack (defaults to filename)")
    p.add_argument(
        "--filename",
        default=None,
        help="Filename sent to Slack (defaults to the basename of --file)",
    )
    p.add_argument(
        "--api-url",
        default=None,
        help="Override SLACK_API_URL for this run (advanced; usually not needed)",
    )
    return p


def _resolve_source_path(args: argparse.Namespace) -> str:
    if args.file and args.image:
        print("Error: pass --file (preferred) or --image, not both.", file=sys.stderr)
        sys.exit(2)
    path = args.file or args.image
    if not path:
        print("Error: --file is required.", file=sys.stderr)
        sys.exit(2)
    return path


def _resolve_token() -> str:
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print("Error: SLACK_BOT_TOKEN env var is required.", file=sys.stderr)
        sys.exit(2)
    return token


def _validate_file(path_arg: str) -> tuple[str, int, str, bytes]:
    path = os.path.abspath(path_arg)
    if not os.path.isfile(path):
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(2)
    length = os.path.getsize(path)
    filename = os.path.basename(path)
    data = Path(path).read_bytes()
    return path, length, filename, data


def _guess_content_type(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


def _step_get_upload_url(client: WebClient, filename: str, length: int) -> tuple[str, str]:
    resp = client.files_getUploadURLExternal(filename=filename, length=length)
    if not resp.get("ok", True):
        err = resp.get("error", "unknown_error")
        print(f"Error: files.getUploadURLExternal failed: {err}", file=sys.stderr)
        sys.exit(1)
    return resp["upload_url"], resp["file_id"]


def _step_put_bytes(upload_url: str, data: bytes, content_type: str) -> None:
    url = upload_url
    for _ in range(2):  # original URL + at most one redirect hop
        req = urllib.request.Request(
            url, data=data, method="POST", headers={"Content-Type": content_type}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                if status // 100 == 2:
                    return
                body = resp.read().decode("utf-8", errors="replace")
                print(f"Error: upload POST returned HTTP {status}: {body}", file=sys.stderr)
                sys.exit(1)
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308) and e.headers is not None:
                location = e.headers.get("Location")
                if location:
                    url = urllib.parse.urljoin(url, location)
                    continue
            body = e.read().decode("utf-8", errors="replace")
            print(f"Error: upload POST returned HTTP {e.code}: {body}", file=sys.stderr)
            sys.exit(1)
        except urllib.error.URLError as e:
            print(f"Error: could not reach upload URL: {e.reason}", file=sys.stderr)
            sys.exit(1)
    print("Error: upload POST followed too many redirects", file=sys.stderr)
    sys.exit(1)


def _step_complete_upload(
    client: WebClient,
    file_id: str,
    title: str,
    channel: str,
    thread_ts: str | None,
    initial_comment: str | None,
) -> dict:
    try:
        resp = client.files_completeUploadExternal(
            files=[{"id": file_id, "title": title}],
            channel_id=channel,
            thread_ts=thread_ts,
            initial_comment=initial_comment,
        )
    except SlackApiError as e:
        err = e.response.get("error", str(e))
        print(f"Error: files.completeUploadExternal failed: {err}", file=sys.stderr)
        sys.exit(1)
    if not resp.get("ok", True):
        err = resp.get("error", "unknown_error")
        print(f"Error: files.completeUploadExternal failed: {err}", file=sys.stderr)
        sys.exit(1)
    return resp


def _do_upload(args: argparse.Namespace) -> int:
    source_path = _resolve_source_path(args)
    _path, length, default_filename, data = _validate_file(source_path)
    token = _resolve_token()

    filename = args.filename or default_filename
    title = args.title or default_filename
    content_type = _guess_content_type(filename)

    api_url = args.api_url or os.environ.get("SLACK_API_URL")
    if api_url:
        base = api_url if api_url.endswith("/") else api_url + "/"
        client = WebClient(token=token, base_url=base)
    else:
        client = WebClient(token=token)

    upload_url, file_id = _step_get_upload_url(client, filename, length)
    _step_put_bytes(upload_url, data, content_type)
    resp = _step_complete_upload(
        client, file_id, title, args.channel, args.thread_ts, args.caption
    )

    files = resp.get("files") or []
    if files:
        first = files[0]
        permalink = first.get("permalink") or first.get("permalink_public") or "(no permalink)"
        print(f"Uploaded file_id={first.get('id', file_id)}")
        print(f"Permalink: {permalink}")
    else:
        print(f"Uploaded file_id={file_id}")
    return 0


def main(argv: list) -> int:
    """Dispatcher entrypoint. argv is the args after the verb."""
    args = build_parser().parse_args(argv)
    return _do_upload(args)
