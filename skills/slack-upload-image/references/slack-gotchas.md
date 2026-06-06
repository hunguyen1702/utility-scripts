# Slack upload gotchas (silent failures)

The 2-step external upload flow has two failure modes that return `ok: true` but leave the file unshared (`channels: []`, `ims: []` in the response). Always inspect the full `files_completeUploadExternal` response during development, not just `ok`.

## 1. Step 2 must be POST, not PUT

The `upload_url` returned by `files.getUploadURLExternal` requires `POST` with the file bytes as the body. `PUT` is accepted (HTTP 200) but the bytes are never parsed — `mimetype` / `filetype` come back empty and step 3 silently skips sharing.

If you ever need to upload manually, use:

```python
import urllib.request
req = urllib.request.Request(upload_url, data=file_bytes, method="POST",
                             headers={"Content-Type": content_type})
urllib.request.urlopen(req)
```

`slack_upload_image.py` already does this correctly.

## 2. `channel_id` must be a resolved Slack ID

`files.completeUploadExternal` takes a channel ID (`C…`, `D…`, `G…`). It does **not** auto-resolve:

- User IDs (`U…`) — works for `chat.postMessage` but fails silently here.
- Channel names like `general` or `#general`.

For DMs, resolve the user to a DM channel ID first:

```python
resp = client.conversations_open(users=user_id)
dm_id = resp["channel"]["id"]  # D…
```

Then pass `dm_id` as `--channel`.

## 3. `files_completeUploadExternal` SDK method name

The Python `slack-sdk` `WebClient` exposes this as `files_completeUploadExternal` (camelCase → snake_case). The Slack API field for the channel is `channel_id`, not `channel`. The `slack_upload_image.py` script already wires both correctly.

## 4. Local emulator limitations

`vercel-labs/emulate` (and most local Slack emulators) do not implement `files.getUploadURLExternal`. Emulator runs will fail at step 1 with a server-side error — this is expected, not a bug in your call. To exercise the script end-to-end, point at real Slack (unset `SLACK_API_URL` / don't pass `--api-url`).

## 5. Inspecting the full response

When debugging, log the full `resp` from `step_complete_upload`, not just `ok`:

```python
import json
print(json.dumps(resp, indent=2))
```

Look for:
- `files[0].channels` and `files[0].ims` — should be non-empty on success.
- `files[0].mimetype` / `filetype` — should match what you uploaded (empty means step 2 silently failed even with HTTP 200).
- `files[0].permalink` — present on success; missing suggests the file was uploaded but not shared.

## Quick checklist when "it uploads but nothing shows up"

1. Did you POST (not PUT) the bytes in step 2?
2. Is `--channel` a `C…` / `D…` / `G…` ID, not a name or `U…`?
3. Is `SLACK_BOT_TOKEN` from an app that has `files:write` scope and is installed in the workspace/channel?
4. For DMs: did you call `conversations.open` first to get a `D…` ID?
5. Is the bot actually a member of a private channel? Public channels usually work; private channels need an explicit invite.
