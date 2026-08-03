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

    if not PENDING_DIR.exists():
        print("No pending directory found, nothing to do.")
        return

    post_dirs = sorted(p for p in PENDING_DIR.iterdir() if p.is_dir())
    if not post_dirs:
        print("No pending posts found.")
        return

    # 在排程模式下，每次只發布 pending 資料夾中的第一篇（動態讀取，不硬編碼起始點）
    if publish_mode == "scheduled":
        post_dirs = post_dirs[:1]  # 每次只發布第一篇
        log_summary(f"[SCHEDULED MODE] Publishing 1 pending post: {post_dirs[0].name}")
    else:
        log_summary(f"[PUSH MODE] Publishing all {len(post_dirs)} pending post(s)")

    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    any_failed = False

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
            dest = PUBLISHED_DIR / post_dir.name
            shutil.move(str(post_dir), str(dest))
            log_summary(f"Moved {post_dir.name} -> {dest}")
        else:
            any_failed = True
            log_summary(f"Left {post_dir.name} in pending/ (will retry next push)")

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
