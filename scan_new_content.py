"""
偵測新素材腳本。
由 .github/workflows/detect-new-content.yml 在 content/** 有新 push 時觸發。

流程：
1. 讀取 content-calendar.yaml + archive.yaml，收集所有「已經被排程表引用過」的檔案路徑
2. 掃描 content/<character>/<年月>/<日期資料夾>/ 底下所有圖片/影片
3. 找出還沒被引用的檔案，依資料夾自動建一筆 status=draft 的項目，加進 content-calendar.yaml
   （caption / hashtags 留空，等待人工或負責生成文案的 agent 補上）

假設的資料夾慣例：content/<character>/<YYYY-MM>/<YYYYMMDD>/<file>
如果日期資料夾名稱抓不到 8 碼日期，date 欄位會留空，需要人工補上。
"""

import re
import yaml
from pathlib import Path

CALENDAR_PATH = "schedule/content-calendar.yaml"
ARCHIVE_PATH = "schedule/archive.yaml"
CONTENT_DIR = Path("content")
MEDIA_EXTENSIONS = {".jpg", ".jpeg", ".png", ".mp4"}


def load_yaml(path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data if data else default


def save_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def collect_referenced_media(calendar, archive):
    referenced = set()
    for post in calendar.get("posts", []) + archive.get("posts", []):
        referenced.update(post.get("media", []))
    return referenced


def guess_date(folder_name):
    match = re.search(r"(\d{8})", folder_name)
    if not match:
        return None
    d = match.group(1)
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def main():
    calendar_path = Path(CALENDAR_PATH)
    archive_path = Path(ARCHIVE_PATH)
    calendar = load_yaml(calendar_path, {"posts": []})
    archive = load_yaml(archive_path, {"posts": []})

    referenced = collect_referenced_media(calendar, archive)
    new_entries = []

    if CONTENT_DIR.exists():
        for date_folder in CONTENT_DIR.glob("*/*/*"):
            if not date_folder.is_dir():
                continue

            media_files = sorted(
                f"{date_folder}/{f.name}"
                for f in date_folder.iterdir()
                if f.suffix.lower() in MEDIA_EXTENSIONS
            )
            unreferenced = [m for m in media_files if m not in referenced]
            if not unreferenced:
                continue

            character = date_folder.parts[-3]
            entry_id = f"{character}-{date_folder.name}"
            new_entries.append(
                {
                    "id": entry_id,
                    "character": character,
                    "date": guess_date(date_folder.name),
                    "platforms": ["instagram"],
                    "caption": "",
                    "hashtags": [],
                    "media": unreferenced,
                    "status": "draft",
                    "scheduled_time": "08:00",
                }
            )

    if not new_entries:
        print("沒有偵測到新素材。")
        return

    calendar.setdefault("posts", []).extend(new_entries)
    save_yaml(calendar_path, calendar)
    print(f"新增 {len(new_entries)} 筆 draft 項目：" + ", ".join(e["id"] for e in new_entries))


if __name__ == "__main__":
    main()
