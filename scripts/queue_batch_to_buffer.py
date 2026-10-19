#!/usr/bin/env python3
"""Queue a batch of social posts to Buffer.

Default mode is dry-run. Live posting must be explicitly requested with --mode live.
Environment:
  BUFFER_API_KEY: Buffer API token
  BUFFER_CHANNEL_IDS: JSON array of Buffer channel IDs
  GITHUB_REPOSITORY: owner/repo used to build public asset URLs
"""
import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

API = "https://api.buffer.com"
PENDING = Path("social-posts/pending")
STATE = Path("docs/buffer-batch-state.json")
BATCH_SIZE = 9
SLOT_WEEKDAYS = (0, 2, 4)  # Monday, Wednesday, Friday
TPE = timezone(timedelta(hours=8))
REF = "main"
CHANNEL_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,128}$")

MUTATION = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess { post { id status dueAt } }
    ... on MutationError { message }
  }
}
"""
CHANNEL_QUERY = """
query ValidateChannel($input: ChannelInput!) {
  channel(input: $input) {
    id name service isDisconnected isLocked isQueuePaused
  }
}
"""


class ConfigurationError(ValueError):
    pass


def parse_args():
    parser = argparse.ArgumentParser(description="Validate and queue Buffer social posts.")
    parser.add_argument(
        "--mode", choices=("dry-run", "live"), default="dry-run",
        help="dry-run validates and previews without creating posts (default); live creates scheduled posts.",
    )
    # Backward-compatible alias; dry-run remains the safe default.
    parser.add_argument("--dry-run", action="store_true", help="Alias for --mode dry-run.")
    return parser.parse_args()


def next_slots(start: date, n: int):
    d, out = start, []
    while len(out) < n:
        if d.weekday() in SLOT_WEEKDAYS:
            out.append(d)
        d += timedelta(days=1)
    return out


def load_channels(raw: str):
    if not raw or not raw.strip():
        raise ConfigurationError("BUFFER_CHANNEL_IDS is empty. Set it to a JSON array of Buffer channel IDs.")
    try:
        channels = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"BUFFER_CHANNEL_IDS is not valid JSON (line {exc.lineno}, column {exc.colno}). "
            'Expected format: ["channel_id_1","channel_id_2"].'
        ) from exc
    if not isinstance(channels, list) or not channels:
        raise ConfigurationError("BUFFER_CHANNEL_IDS must be a non-empty JSON array.")
    if any(not isinstance(ch, str) or not ch.strip() for ch in channels):
        raise ConfigurationError("Every BUFFER_CHANNEL_IDS entry must be a non-empty string.")
    channels = [ch.strip() for ch in channels]
    invalid = [ch for ch in channels if not CHANNEL_ID_RE.fullmatch(ch)]
    if invalid:
        raise ConfigurationError(
            "One or more channel IDs contain invalid characters or have an unexpected length. "
            "Use the ID from the Buffer channel URL/API; do not include a URL or extra punctuation."
        )
    if len(channels) != len(set(channels)):
        raise ConfigurationError("BUFFER_CHANNEL_IDS contains duplicate IDs; remove duplicates.")
    return channels


def buffer_request(key, query, variables):
    try:
        response = requests.post(
            API,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"query": query, "variables": variables},
            timeout=30,
        )
    except requests.RequestException as exc:
        raise ConfigurationError(f"Could not reach Buffer API: {exc.__class__.__name__}") from exc
    if response.status_code != 200:
        # Do not print response body; it may contain details not suitable for logs.
        raise ConfigurationError(f"Buffer API returned HTTP {response.status_code}. Check token permissions and API status.")
    try:
        payload = response.json()
    except ValueError as exc:
        raise ConfigurationError("Buffer API returned a non-JSON response.") from exc
    if payload.get("errors"):
        messages = [
            str(item.get("message", "GraphQL error"))[:180]
            for item in payload["errors"] if isinstance(item, dict)
        ]
        raise ConfigurationError("Buffer API GraphQL error: " + "; ".join(messages))
    return payload.get("data") or {}


def validate_channels(key, channels, live):
    if not key:
        if live:
            raise ConfigurationError("BUFFER_API_KEY is missing or empty; live mode is blocked.")
        print("WARNING: BUFFER_API_KEY is missing; channel IDs were format-checked only, not verified against Buffer.")
        return
    for channel_id in channels:
        data = buffer_request(key, CHANNEL_QUERY, {"input": {"id": channel_id}})
        channel = data.get("channel")
        if not channel or channel.get("id") != channel_id:
            raise ConfigurationError(f"Buffer did not return the requested channel ID {channel_id}.")
        label = channel.get("name") or channel_id
        service = channel.get("service") or "unknown service"
        print(f"Channel OK: {label} ({service}) [{channel_id}]")
        if channel.get("isDisconnected"):
            raise ConfigurationError(f"Buffer channel {channel_id} is disconnected; reconnect it in Buffer first.")
        if channel.get("isLocked"):
            raise ConfigurationError(f"Buffer channel {channel_id} is locked; resolve the channel/plan issue first.")
        if channel.get("isQueuePaused"):
            raise ConfigurationError(f"Buffer channel {channel_id} has its queue paused; unpause it before scheduling.")


def load_state():
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigurationError(f"Cannot read {STATE}: {exc.__class__.__name__}") from exc
    if not isinstance(state, dict) or not isinstance(state.get("queued"), list):
        raise ConfigurationError(f"{STATE} must contain an object with a queued array.")
    try:
        last_slot = date.fromisoformat(state["last_slot_date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ConfigurationError(f"{STATE} has an invalid last_slot_date.") from exc
    return state, last_slot


def load_batch(todo, slots, repo):
    batch_data = []
    for folder, day in zip(todo, slots):
        manifest_path = folder / "publish.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigurationError(f"{folder.name}: cannot read valid publish.json ({exc.__class__.__name__}).") from exc
        text = manifest.get("text")
        images = manifest.get("images")
        if not isinstance(text, str) or not text.strip():
            raise ConfigurationError(f"{folder.name}: publish.json needs non-empty text.")
        if not isinstance(images, list) or not images:
            raise ConfigurationError(f"{folder.name}: publish.json needs a non-empty images array.")
        urls = []
        for item in images:
            if not isinstance(item, str) or not item.strip():
                raise ConfigurationError(f"{folder.name}: every image entry must be a relative file path.")
            relative = Path(item)
            if relative.is_absolute() or ".." in relative.parts:
                raise ConfigurationError(f"{folder.name}: image path must stay inside the post folder.")
            if not (folder / relative).is_file():
                raise ConfigurationError(f"{folder.name}: image file not found: {item}")
            urls.append(f"https://raw.githubusercontent.com/{repo}/{REF}/{folder.as_posix()}/{item}")
        due = f"{day.isoformat()}T08:05:00+08:00"
        batch_data.append({"folder": folder, "text": text, "urls": urls, "due": due, "day": day})
    return batch_data


def create_post(key, channel, text, urls, due):
    # Avoid hard-coding Facebook metadata: channel service is validated separately and
    # Buffer's default post metadata is preferable for cross-channel compatibility.
    inp = {
        "text": text,
        "channelId": channel,
        "assets": [{"image": {"url": url}} for url in urls],
        "schedulingType": "automatic",
        "mode": "customScheduled",
        "dueAt": due,
    }
    data = buffer_request(key, MUTATION, {"input": inp})
    result = data.get("createPost") or {}
    post = result.get("post")
    if post:
        return post
    return None


def main():
    args = parse_args()
    mode = "dry-run" if args.dry_run else args.mode
    live = mode == "live"

    key = os.environ.get("BUFFER_API_KEY", "").strip()
    raw_channels = os.environ.get("BUFFER_CHANNEL_IDS", "")
    channels = load_channels(raw_channels)
    if not key and live:
        raise ConfigurationError("BUFFER_API_KEY is missing or empty; live mode is blocked.")
    validate_channels(key, channels, live)

    state, last_slot = load_state()
    today = datetime.now(TPE).date()
    if today <= last_slot:
        print(f"Previous batch ends on {last_slot}; today is {today}. Nothing to queue.")
        return 0

    done = set(state["queued"])
    try:
        folders = sorted(p for p in PENDING.iterdir() if p.is_dir() and p.name not in done)
    except OSError as exc:
        raise ConfigurationError(f"Cannot list pending posts: {exc.__class__.__name__}") from exc
    if not folders:
        print("No unqueued posts remain.")
        return 0

    batch = folders[:BATCH_SIZE]
    start = max(today + timedelta(days=1), last_slot + timedelta(days=1))
    slots = next_slots(start, len(batch))
    repo = os.environ.get("GITHUB_REPOSITORY", "bioitrust0414-collab/aquar_9669")
    posts = load_batch(batch, slots, repo)

    print(f"Mode: {mode}; channels: {len(channels)}; posts in this batch: {len(posts)}.")
    for item in posts:
        print(f"{'[DRY-RUN] ' if not live else '[LIVE] '}{item['folder'].name} -> {item['due']} ({len(item['urls'])} image(s))")
    if not live:
        print("Dry-run complete. No Buffer posts were created and state was not changed.")
        return 0

    for item in posts:
        created = []
        for channel in channels:
            try:
                post = create_post(key, channel, item["text"], item["urls"], item["due"])
            except ConfigurationError as exc:
                print(f"FAIL {item['folder'].name} -> {item['due']} channel={channel}: {exc}", file=sys.stderr)
                print("Stopped immediately. Check Buffer before retrying because a previous channel may already have accepted this post.", file=sys.stderr)
                return 1
            if not post:
                print(f"FAIL {item['folder'].name} -> {item['due']} channel={channel}: Buffer returned no post.", file=sys.stderr)
                print("Stopped immediately. Check Buffer before retrying because a previous channel may already have accepted this post.", file=sys.stderr)
                return 1
            created.append({"channel_id": channel, "post_id": post.get("id"), "status": post.get("status"), "due_at": post.get("dueAt")})
            print(f"OK {item['folder'].name} -> {item['due']} channel={channel} post_id={post.get('id')} status={post.get('status')}")

        # Record only after all channels accepted the post. Persist immediately after each post.
        state["queued"].append(item["folder"].name)
        state.setdefault("buffer_posts", {})[item["folder"].name] = created
        state["last_slot_date"] = item["day"].isoformat()
        state["last_batch_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Live queue operation completed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConfigurationError as exc:
        print(f"CONFIGURATION ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
