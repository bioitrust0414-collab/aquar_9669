#!/usr/bin/env python3
"""
每 3 週排一批（9 篇），每週一三五 08:05 (Asia/Taipei) 發布。
- 以 docs/buffer-batch-state.json 為唯一依據，不再用 pending/published 資料夾判斷是否已發。
- 一批 9 篇 = 3 週 x 3 天；Buffer 方案排程上限 10 篇，所以必須等上一批發完才排下一批。
- 每週日由 GitHub Actions 觸發；只有「今天 > 上一批最後一個發文日」才會真的排程。

env: BUFFER_API_KEY, BUFFER_CHANNEL_IDS(JSON array), GITHUB_REPOSITORY
用法: python scripts/queue_batch_to_buffer.py [--dry-run]
"""
import json, os, sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import requests

API = "https://api.buffer.com"
PENDING = Path("social-posts/pending")
STATE = Path("docs/buffer-batch-state.json")
BATCH_SIZE = 9
SLOT_WEEKDAYS = (0, 2, 4)  # 週一、三、五
TPE = timezone(timedelta(hours=8))
REF = "main"  # 圖片一律從 main 讀取

MUTATION = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess { post { id status dueAt } }
    ... on MutationError { message }
  }
}
"""


def next_slots(start: date, n: int):
    d, out = start, []
    while len(out) < n:
        if d.weekday() in SLOT_WEEKDAYS:
            out.append(d)
        d += timedelta(days=1)
    return out


def create_post(key, channel, text, urls, due):
    inp = {
        "text": text, "channelId": channel,
        "assets": [{"image": {"url": u}} for u in urls],
        "metadata": {"facebook": {"type": "post"}},
        "schedulingType": "automatic", "mode": "customScheduled", "dueAt": due,
    }
    r = requests.post(API, headers={"Authorization": f"Bearer {key}"},
                      json={"query": MUTATION, "variables": {"input": inp}}, timeout=60)
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}: {r.text[:300]}"
    d = r.json()
    if d.get("errors"):
        return False, str(d["errors"])[:300]
    res = (d.get("data") or {}).get("createPost") or {}
    return ("post" in res and bool(res["post"])), res.get("post") or res.get("message")


def main():
    dry = "--dry-run" in sys.argv
    state = json.loads(STATE.read_text(encoding="utf-8"))
    today = datetime.now(TPE).date()
    last_slot = date.fromisoformat(state["last_slot_date"])
    if today <= last_slot:
        print(f"上一批排到 {last_slot}，今天 {today}，尚未到期，略過。")
        return
    done = set(state["queued"])
    todo = [p for p in sorted(PENDING.iterdir()) if p.is_dir() and p.name not in done]
    if not todo:
        print("沒有尚未排程的貼文了。"); return
    batch = todo[:BATCH_SIZE]
    start = max(today + timedelta(days=1), last_slot + timedelta(days=1))
    slots = next_slots(start, len(batch))

    key = os.environ.get("BUFFER_API_KEY", "")
    channels = json.loads(os.environ.get("BUFFER_CHANNEL_IDS", "[]"))
    repo = os.environ.get("GITHUB_REPOSITORY", "bioitrust0414-collab/aquar_9669")
    failed = False
    for folder, day in zip(batch, slots):
        m = json.loads((folder / "publish.json").read_text(encoding="utf-8"))
        urls = [f"https://raw.githubusercontent.com/{repo}/{REF}/{folder.as_posix()}/{i}" for i in m["images"]]
        due = f"{day.isoformat()}T08:05:00+08:00"
        if dry:
            print(f"[dry-run] {folder.name} -> {due}"); continue
        ok = True
        for ch in channels:
            ok_i, info = create_post(key, ch, m["text"], urls, due)
            print(("OK  " if ok_i else "FAIL"), folder.name, due, ch, info)
            ok = ok and ok_i
        if not ok:
            failed = True
            break  # 失敗就停，避免順序錯亂；下次執行會從失敗那篇接續
        state["queued"].append(folder.name)
        state["last_slot_date"] = day.isoformat()
        state["last_batch_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
