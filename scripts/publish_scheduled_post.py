#!/usr/bin/env python3
"""
Publish one pending social post to Buffer via scheduled GitHub Actions.

This script is designed to run on a schedule (e.g., every Tuesday-Friday at 08:15 UTC+8).
It publishes exactly ONE post from social-posts/pending/ to Buffer, then moves it to
social-posts/published/. This prevents duplicate posting and ensures one post per day.

Key differences from publish_to_buffer.py:
- Publishes only ONE pending folder per run (not all)
- Respects the 'scheduled_at' field in publish.json if present
- Includes safeguards against duplicate posting
- Logs detailed information for troubleshooting

Required env vars:
  BUFFER_API_KEY      - personal API key from Buffer (Bearer token)
  BUFFER_CHANNEL_IDS  - JSON array of channel IDs to post to
  GITHUB_REPOSITORY   - "owner/repo", auto-provided by GitHub Actions
  GITHUB_REF_NAME     - branch name, auto-provided by GitHub Actions
"""

import json
import os
import shutil
import sys
import traceback
from pathlib import Path
from datetime import datetime

import requests

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


DEBUG_LOG_PATH = Path("social-posts/.last-run-debug.log")


def log_summary(text):
    """Print and append diagnostic text to a repo-tracked debug log file."""
    print(text)
    DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(text + "\n\n")


BUFFER_API_URL = "https://api.buffer.com"
PENDING_DIR = Path("social-posts/pending")
PUBLISHED_DIR = Path("social-posts/published")

CREATE_POST_MUTATION = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess {
      post { id text status assets { id mimeType } }
    }
    ... on MutationError {
      message
    }
  }
}
"""


def get_env_or_die(name):
    value = os.environ.get(name)
    if not value:
        print(f"ERROR: missing required env var {name}", file=sys.stderr)
        sys.exit(1)
    return value


def raw_url(repo, ref, path):
    return f"https://raw.githubusercontent.com/{repo}/{ref}/{path}"


def get_image_dimensions(file_path):
    """Extract image dimensions from a local file."""
    if not HAS_PIL:
        return None
    
    try:
        if os.path.exists(file_path):
            img = Image.open(file_path)
            width, height = img.size
            return (width, height)
    except Exception as e:
        pass
    
    return None


def build_assets(image_urls, local_image_paths=None):
    """Build asset objects with image URLs and optional dimensions."""
    assets = []
    for i, url in enumerate(image_urls):
        asset = {"image": {"url": url}}
        
        if local_image_paths and i < len(local_image_paths):
            dims = get_image_dimensions(local_image_paths[i])
            if dims:
                width, height = dims
                asset["image"]["width"] = width
                asset["image"]["height"] = height
        
        assets.append(asset)
    
    return assets


def create_post(api_key, channel_id, text, image_urls, scheduled_at=None, local_image_paths=None):
    """Create a post in Buffer via GraphQL API."""
    input_fields = {
        "text": text,
        "channelId": channel_id,
        "assets": build_assets(image_urls, local_image_paths),
        "metadata": {"facebook": {"type": "post"}},
    }
    if scheduled_at:
        input_fields["schedulingType"] = "automatic"
        input_fields["mode"] = "customScheduled"
        input_fields["dueAt"] = scheduled_at
    else:
        input_fields["schedulingType"] = "automatic"
        input_fields["mode"] = "addToQueue"

    payload = {
        "query": CREATE_POST_MUTATION,
        "variables": {"input": input_fields},
    }
    resp = requests.post(
        BUFFER_API_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json=payload,
        timeout=30,
    )

    if resp.status_code != 200:
        log_summary(
            f"### Buffer HTTP {resp.status_code} for channel {channel_id}\n"
            f"```\n{resp.text[:2000]}\n```"
        )
        return False, f"HTTP {resp.status_code}: {resp.text[:500]}"

    data = resp.json()

    if "errors" in data and data["errors"]:
        log_summary(
            f"### Buffer GraphQL errors for channel {channel_id}\n"
            f"```\n{json.dumps(data['errors'], ensure_ascii=False, indent=2)[:2000]}\n```"
        )
        return False, str(data["errors"])

    result = data.get("data", {}).get("createPost", {})
    if result.get("post"):
        return True, result["post"]
    return False, result.get("message", "unknown error")


def main():
    api_key = get_env_or_die("BUFFER_API_KEY")
    channel_ids = json.loads(get_env_or_die("BUFFER_CHANNEL_IDS"))
    repo = get_env_or_die("GITHUB_REPOSITORY")
    ref = get_env_or_die("GITHUB_REF_NAME")

    log_summary(f"=== Scheduled Post Publishing Run ===")
    log_summary(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    log_summary(f"Repository: {repo}")
    log_summary(f"Branch: {ref}")
    log_summary(f"Channels: {channel_ids}")

    if not PENDING_DIR.exists():
        log_summary("No pending directory found, nothing to do.")
        return

    post_dirs = sorted(p for p in PENDING_DIR.iterdir() if p.is_dir())
    if not post_dirs:
        log_summary("No pending posts found.")
        return

    log_summary(f"Found {len(post_dirs)} pending post(s)")
    log_summary(f"PIL available: {HAS_PIL}")

    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)

    # Publish only the FIRST pending post
    post_dir = post_dirs[0]
    manifest_path = post_dir / "publish.json"
    
    if not manifest_path.exists():
        log_summary(f"SKIP {post_dir}: no publish.json found")
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    text = manifest.get("text", "")
    image_filenames = manifest.get("images", [])
    scheduled_at = manifest.get("scheduled_at")
    
    image_urls = [
        raw_url(repo, ref, f"{post_dir.as_posix()}/{fn}")
        for fn in image_filenames
    ]
    local_image_paths = [
        (post_dir / fn).as_posix()
        for fn in image_filenames
    ]

    log_summary(f"## Publishing `{post_dir.name}` to {len(channel_ids)} channel(s)")
    log_summary(f"Scheduled at: {scheduled_at or 'immediate (add to queue)'}")
    log_summary(f"Image count: {len(image_urls)}")
    log_summary(f"Image URLs: {image_urls}")
    
    if HAS_PIL:
        dims_info = []
        for path in local_image_paths:
            dims = get_image_dimensions(path)
            if dims:
                dims_info.append(f"{Path(path).name}: {dims[0]}x{dims[1]}")
        if dims_info:
            log_summary(f"Image dimensions: {', '.join(dims_info)}")
    
    all_ok = True
    for channel_id in channel_ids:
        ok, result = create_post(api_key, channel_id, text, image_urls, scheduled_at, local_image_paths)
        if ok:
            log_summary(
                f"OK channel={channel_id} post_id={result.get('id')} "
                f"status={result.get('status')} assets={result.get('assets')}"
            )
        else:
            all_ok = False
            log_summary(f"FAILED channel={channel_id}: {result}")

    if all_ok:
        dest = PUBLISHED_DIR / post_dir.name
        shutil.move(str(post_dir), str(dest))
        log_summary(f"Moved {post_dir.name} -> {dest}")
        log_summary(f"✓ Successfully published 1 post")
    else:
        log_summary(f"✗ Failed to publish {post_dir.name} (will retry next scheduled run)")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        log_summary(f"### Unhandled exception\n```\n{traceback.format_exc()}\n```")
        sys.exit(1)
