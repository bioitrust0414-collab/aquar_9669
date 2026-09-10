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

IMPROVEMENT: This version extracts image dimensions from local files
before publishing, ensuring Buffer can properly display image previews
and metadata.

Scheduled mode (PUBLISH_MODE=scheduled) runs a 21-day batch cycle: the
workflow's cron fires daily, but this script only actually dispatches a
batch once BATCH_INTERVAL_DAYS have elapsed since the last one (tracked
in BATCH_STATE_PATH) - otherwise it's a no-op. When a batch is due, it
takes the next BATCH_SIZE pending posts and assigns each an evenly
spread scheduled_at across the batch window, so Buffer releases them
gradually instead of this script creating BATCH_SIZE posts back-to-back
against Buffer's own rate limit. FORCE_BATCH=true (set for
workflow_dispatch) skips the day-count wait and dispatches immediately.

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
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


DEBUG_LOG_PATH = Path("social-posts/.last-run-debug.log")


def log_summary(text):
    """Print and append diagnostic text to a repo-tracked debug log file.

    (GITHUB_STEP_SUMMARY is not retrievable via the GitHub API, only in
    the web UI, so writing to a tracked file that the workflow commits
    back is the only way to inspect run output outside the browser.)
    """
    print(text)
    DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(text + "\n\n")

BUFFER_API_URL = "https://api.buffer.com"
PENDING_DIR = Path("social-posts/pending")
PUBLISHED_DIR = Path("social-posts/published")

BATCH_STATE_PATH = Path("docs/buffer-batch-state.json")
BATCH_INTERVAL_DAYS = 21
BATCH_SIZE = 10

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


def load_batch_state():
    if BATCH_STATE_PATH.exists():
        return json.loads(BATCH_STATE_PATH.read_text(encoding="utf-8"))
    return {"last_batch_at": None}


def save_batch_state(state):
    BATCH_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BATCH_STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def spread_scheduled_times(count, start):
    """Evenly spread `count` datetimes across the BATCH_INTERVAL_DAYS window starting at `start`."""
    spacing = timedelta(days=BATCH_INTERVAL_DAYS / count)
    return [start + spacing * i for i in range(count)]


def get_image_dimensions(file_path):
    """Extract image dimensions from a local file.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Tuple of (width, height) or None if extraction fails
    """
    if not HAS_PIL:
        return None
    
    try:
        if os.path.exists(file_path):
            img = Image.open(file_path)
            width, height = img.size
            return (width, height)
    except Exception as e:
        # Silently skip on error - Buffer will handle missing dimensions
        pass
    
    return None


def build_assets(image_urls, local_image_paths=None):
    """Build asset objects with image URLs and optional dimensions.
    
    Args:
        image_urls: List of remote image URLs (raw.githubusercontent.com)
        local_image_paths: Optional list of local file paths for dimension extraction
    
    Returns:
        List of asset objects with URL and optional width/height
    """
    assets = []
    for i, url in enumerate(image_urls):
        asset = {"image": {"url": url}}
        
        # If local paths provided, try to extract dimensions
        if local_image_paths and i < len(local_image_paths):
            dims = get_image_dimensions(local_image_paths[i])
            if dims:
                width, height = dims
                asset["image"]["width"] = width
                asset["image"]["height"] = height
        
        assets.append(asset)
    
    return assets


def create_post(api_key, channel_id, text, image_urls, scheduled_at=None, local_image_paths=None):
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
    publish_mode = os.environ.get("PUBLISH_MODE", "all")  # 'scheduled' or 'all'
    force_batch = os.environ.get("FORCE_BATCH", "false").lower() == "true"

    if not PENDING_DIR.exists():
        print("No pending directory found, nothing to do.")
        return

    post_dirs = sorted(p for p in PENDING_DIR.iterdir() if p.is_dir())
    if not post_dirs:
        print("No pending posts found.")
        return

    now = datetime.now(timezone.utc)

    if publish_mode == "scheduled":
        state = load_batch_state()
        last_batch_at = state.get("last_batch_at")

        if last_batch_at is None:
            reason = "first run"
        elif force_batch:
            reason = "forced via workflow_dispatch"
        else:
            days_elapsed = (now - datetime.fromisoformat(last_batch_at)).total_seconds() / 86400
            if days_elapsed < BATCH_INTERVAL_DAYS:
                log_summary(
                    f"[SCHEDULED MODE] {days_elapsed:.1f} of {BATCH_INTERVAL_DAYS} days elapsed "
                    f"since last batch ({last_batch_at}); not due yet, skipping."
                )
                return
            reason = f"{days_elapsed:.1f} days elapsed since last batch"

        post_dirs = post_dirs[:BATCH_SIZE]

        # Assign each post in the batch an evenly spread scheduled_at instead
        # of creating BATCH_SIZE posts back-to-back (that burst is what
        # tripped Buffer's per-client rate limit in push mode before).
        # Buffer then releases them gradually on its own schedule.
        scheduled_times = spread_scheduled_times(len(post_dirs), now + timedelta(minutes=5))
        for post_dir, sched in zip(post_dirs, scheduled_times):
            manifest_path = post_dir / "publish.json"
            if not manifest_path.exists():
                continue
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["scheduled_at"] = sched.strftime("%Y-%m-%dT%H:%M:%SZ")
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        log_summary(
            f"[SCHEDULED MODE] Batch due ({reason}). Dispatching {len(post_dirs)} post(s), "
            f"spread across the next {BATCH_INTERVAL_DAYS} days: {[d.name for d in post_dirs]}"
        )
    else:
        log_summary(f"[PUSH MODE] Publishing all {len(post_dirs)} pending post(s)")

    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    any_failed = False
    published_count = 0

    # Log PIL availability
    if HAS_PIL:
        log_summary("✓ PIL available - image dimensions will be extracted\n")
    else:
        log_summary("⚠ PIL not available - image dimensions will not be extracted\n")

    for post_dir in post_dirs:
        manifest_path = post_dir / "publish.json"
        if not manifest_path.exists():
            print(f"SKIP {post_dir}: no publish.json found")
            any_failed = True
            continue

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        text = manifest.get("text", "")
        image_filenames = manifest.get("images", [])
        scheduled_at = manifest.get("scheduled_at")
        image_urls = [
            raw_url(repo, ref, f"{post_dir.as_posix()}/{fn}")
            for fn in image_filenames
        ]
        # Build local image paths for dimension extraction
        local_image_paths = [
            (post_dir / fn).as_posix()
            for fn in image_filenames
        ]

        log_summary(f"## Publishing `{post_dir.name}` to {len(channel_ids)} channel(s)")
        log_summary(f"Image URLs: {image_urls}")
        
        # Log dimensions if available
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
            manifest["published_at"] = datetime.now(timezone.utc).isoformat()
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            dest = PUBLISHED_DIR / post_dir.name
            shutil.move(str(post_dir), str(dest))
            log_summary(f"Moved {post_dir.name} -> {dest}")
            published_count += 1
        else:
            any_failed = True
            log_summary(f"Left {post_dir.name} in pending/ (will retry next push)")

    if publish_mode == "scheduled":
        if published_count > 0:
            save_batch_state({"last_batch_at": now.strftime("%Y-%m-%dT%H:%M:%SZ")})
            log_summary(
                f"[SCHEDULED MODE] {published_count}/{len(post_dirs)} post(s) in this batch "
                f"succeeded; batch state advanced, next batch due in {BATCH_INTERVAL_DAYS} days."
            )
        else:
            log_summary(
                "[SCHEDULED MODE] No posts in this batch succeeded; batch state NOT advanced, "
                "will retry the whole batch on the next scheduled run."
            )

    if any_failed:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        log_summary(f"### Unhandled exception\n```\n{traceback.format_exc()}\n```")
        sys.exit(1)
