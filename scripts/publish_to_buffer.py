"""
Publish pending social posts to Buffer via the current (2026) GraphQL API.

Reads every folder under social-posts/pending/, posts each to every
channel ID in BUFFER_CHANNEL_IDS via Buffer's createPost mutation
(https://api.buffer.com), then moves successfully-published folders to
social-posts/published/.

Images are referenced by their raw.githubusercontent.com URL rather than
uploaded directly - Buffer's API does not accept direct file uploads and
requires a publicly reachable media URL. This only works because this
repo is public; if the repo is ever made private, these URLs will stop
resolving for Buffer and posts with images will fail.

Required env vars:
  BUFFER_API_KEY      - personal API key from Buffer (Bearer token, NOT
                         the old OAuth "access_token")
  BUFFER_CHANNEL_IDS  - JSON array of channel IDs to post to, e.g.
                         ["6a605f5ee2638b94d7b1e3fe"]
  GITHUB_REPOSITORY   - "owner/repo", auto-provided by GitHub Actions
  GITHUB_REF_NAME     - branch name, auto-provided by GitHub Actions
"""

import json
import os
import shutil
import sys
from pathlib import Path

import requests

BUFFER_API_URL = "https://api.buffer.com"
PENDING_DIR = Path("social-posts/pending")
PUBLISHED_DIR = Path("social-posts/published")

CREATE_POST_MUTATION = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess {
      post { id text status }
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


def build_assets(image_urls):
    return [{"image": {"url": url}} for url in image_urls]


def create_post(api_key, channel_id, text, image_urls):
    payload = {
        "query": CREATE_POST_MUTATION,
        "variables": {
            "input": {
                "text": text,
                "channelId": channel_id,
                "schedulingType": "automatic",
                "mode": "addToQueue",
                "assets": build_assets(image_urls),
            }
        },
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
    resp.raise_for_status()
    data = resp.json()

    if "errors" in data and data["errors"]:
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

    if not PENDING_DIR.exists():
        print("No pending directory found, nothing to do.")
        return

    post_dirs = sorted(p for p in PENDING_DIR.iterdir() if p.is_dir())
    if not post_dirs:
        print("No pending posts found.")
        return

    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    any_failed = False

    for post_dir in post_dirs:
        manifest_path = post_dir / "publish.json"
        if not manifest_path.exists():
            print(f"SKIP {post_dir}: no publish.json found")
            any_failed = True
            continue

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        text = manifest.get("text", "")
        image_filenames = manifest.get("images", [])
        image_urls = [
            raw_url(repo, ref, f"{post_dir.as_posix()}/{fn}")
            for fn in image_filenames
        ]

        print(f"Publishing {post_dir.name} to {len(channel_ids)} channel(s)...")
        all_ok = True
        for channel_id in channel_ids:
            ok, result = create_post(api_key, channel_id, text, image_urls)
            if ok:
                print(f"  OK channel={channel_id} post_id={result.get('id')}")
            else:
                all_ok = False
                print(f"  FAILED channel={channel_id}: {result}", file=sys.stderr)

        if all_ok:
            dest = PUBLISHED_DIR / post_dir.name
            shutil.move(str(post_dir), str(dest))
            print(f"  Moved {post_dir.name} -> {dest}")
        else:
            any_failed = True
            print(f"  Left {post_dir.name} in pending/ (will retry next push)")

    if any_failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
