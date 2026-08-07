"""
Push the next pieces (in v3 sequence order) into aquar-digest's data/
folder via the GitHub Contents API, so the site can read them locally
at build time instead of calling the GitHub API at runtime.

v3 order source of truth: social-posts/published/ + social-posts/pending/
folder names (aquar-NNN-<slug>) — the same ordering already used to
queue posts to Buffer, sorted by their numeric prefix.

Per run, pushes PUSH_COUNT pieces (default 2) starting from the position
recorded in docs/digest-push-state.json, then advances that state.

Required secrets/env vars:
  DIGEST_REPO_TOKEN  - PAT with contents:write on bioitrust0414-collab/aquar-digest
  PUSH_COUNT         - optional, defaults to 2
"""

import base64
import json
import os
import re
import sys
from pathlib import Path

import requests

DIGEST_REPO = "bioitrust0414-collab/aquar-digest"
GITHUB_API = "https://api.github.com"
STATE_PATH = Path("docs/digest-push-state.json")
SCHEDULE_PATH = Path("docs/publish-schedule.json")
SOCIAL_DIRS = [Path("social-posts/published"), Path("social-posts/pending")]

FOLDER_RE = re.compile(r"^aquar-(\d+)-(.+)$")


def get_env_or_die(name):
    value = os.environ.get(name)
    if not value:
        print(f"ERROR: missing required env var {name}", file=sys.stderr)
        sys.exit(1)
    return value


def load_v3_order():
    """Return [(sequence_num, slug), ...] sorted by the aquar-NNN prefix."""
    entries = []
    seen = set()
    for d in SOCIAL_DIRS:
        if not d.exists():
            continue
        for p in sorted(d.iterdir()):
            if not p.is_dir():
                continue
            m = FOLDER_RE.match(p.name)
            if m:
                num = int(m.group(1))
                if num not in seen:
                    seen.add(num)
                    entries.append((num, m.group(2)))
    entries.sort(key=lambda x: x[0])
    return entries


def load_schedule_lookup():
    """topic_folder basename -> full schedule entry (from docs/publish-schedule.json)."""
    data = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
    return {entry["topic_folder"].split("/")[-1]: entry for entry in data["schedule"]}


def gh_get(path, token):
    return requests.get(
        f"{GITHUB_API}/repos/{DIGEST_REPO}/contents/{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        timeout=30,
    )


def gh_put(path, content_bytes, message, token, sha=None):
    body = {"message": message, "content": base64.b64encode(content_bytes).decode("ascii")}
    if sha:
        body["sha"] = sha
    res = requests.put(
        f"{GITHUB_API}/repos/{DIGEST_REPO}/contents/{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json=body,
        timeout=30,
    )
    if res.status_code not in (200, 201):
        raise RuntimeError(f"PUT {path} failed [{res.status_code}]: {res.text[:500]}")
    return res.json()


def push_schedule_entry(token, v3_entry):
    """Fetch current data/schedule.json from digest repo, upsert this entry, PUT back."""
    res = gh_get("data/schedule.json", token)
    if res.status_code == 200:
        current = res.json()
        sha = current["sha"]
        content = json.loads(base64.b64decode(current["content"]).decode("utf-8"))
    elif res.status_code == 404:
        sha = None
        content = {
            "repo": "bioitrust0414-collab/aquar_9669",
            "brand": "Aquar",
            "generated_note": "Synced from aquar_9669 by push_to_digest.py",
            "total_pieces": 59,
            "fully_ready": 0,
            "ready_with_accepted_gap": 0,
            "needs_attention": 0,
            "schedule": [],
        }
    else:
        raise RuntimeError(f"GET data/schedule.json failed [{res.status_code}]: {res.text[:500]}")

    content["schedule"] = [
        e for e in content["schedule"] if e["topic_folder"] != v3_entry["topic_folder"]
    ]
    content["schedule"].append(v3_entry)
    content["schedule"].sort(key=lambda e: e["sequence"])

    body = json.dumps(content, ensure_ascii=False, indent=2).encode("utf-8")
    gh_put("data/schedule.json", body, f"Sync schedule entry: {v3_entry['topic_folder']}", token, sha)


def push_copy_md(token, topic_folder):
    local_path = Path("content") / topic_folder / "copy.md"
    content_bytes = local_path.read_bytes()
    remote_path = f"data/content/{topic_folder}/copy.md"
    res = gh_get(remote_path, token)
    sha = res.json()["sha"] if res.status_code == 200 else None
    gh_put(remote_path, content_bytes, f"Sync copy: {topic_folder}", token, sha)


def push_images_manifest(token, topic_folder, images_present):
    remote_path = f"data/content/{topic_folder}/images.json"
    body = json.dumps(images_present, ensure_ascii=False, indent=2).encode("utf-8")
    res = gh_get(remote_path, token)
    sha = res.json()["sha"] if res.status_code == 200 else None
    gh_put(remote_path, body, f"Sync image manifest: {topic_folder}", token, sha)


def main():
    token = get_env_or_die("DIGEST_REPO_TOKEN")
    push_count = int(os.environ.get("PUSH_COUNT", "2"))

    v3_order = load_v3_order()
    if not v3_order:
        print("No social-posts folders found, nothing to sync.")
        return

    schedule_lookup = load_schedule_lookup()

    state = {"last_pushed_index": 0}
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))

    # Write the state file immediately so it always exists on disk, even if
    # a later API call fails partway through — otherwise the "Commit updated
    # push state" workflow step has nothing to git add and errors out too.
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    start = state["last_pushed_index"]
    batch = v3_order[start:start + push_count]
    if not batch:
        print("All pieces already synced to digest.")
        return

    pushed = 0
    for num, slug in batch:
        entry = schedule_lookup.get(slug)
        if not entry:
            print(f"WARN: no schedule.json entry found for slug '{slug}', skipping")
            continue
        v3_entry = dict(entry)
        v3_entry["sequence"] = num  # re-number to match v3 (aquar-NNN) order
        print(f"Pushing #{num} {entry['topic_folder']} to digest...")
        push_schedule_entry(token, v3_entry)
        push_copy_md(token, entry["topic_folder"])
        push_images_manifest(token, entry["topic_folder"], entry.get("images_present", []))
        pushed += 1

    state["last_pushed_index"] = start + len(batch)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Synced {pushed} piece(s). last_pushed_index={state['last_pushed_index']}")


if __name__ == "__main__":
    main()
