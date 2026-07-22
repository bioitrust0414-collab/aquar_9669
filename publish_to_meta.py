"""
每日發布腳本。
由 .github/workflows/publish.yml 排程呼叫。

流程：
1. 讀 schedule/content-calendar.yaml，找出 date == 今天 且 status == "ready" 的貼文
2. 透過 Meta Graph API 發布到 Instagram
3. 成功後，把該筆從 content-calendar.yaml 移除，加進 schedule/archive.yaml（附發布時間與 media id）
4. 若找不到符合條件的貼文，或呼叫失敗，會印出訊息並以非 0 結束碼結束（方便在 Actions 上看到失敗）

需要的環境變數：
- META_PAGE_TOKEN：長效 Page/IG Access Token
- IG_USER_ID：Instagram Business 帳號的 user id
"""

import os
import sys
import datetime
import yaml
import requests

REPO_RAW_BASE = "https://raw.githubusercontent.com/bioitrust0414-collab/momo_daily/main/"
CALENDAR_PATH = "schedule/content-calendar.yaml"
ARCHIVE_PATH = "schedule/archive.yaml"
GRAPH_API_VERSION = "v20.0"


def load_yaml(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data if data else default


def save_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def find_todays_post(calendar):
    today = datetime.date.today().isoformat()
    for post in calendar.get("posts", []):
        if post.get("date") == today and post.get("status") == "ready":
            return post
    return None


def publish_single_image(post, token, ig_user_id):
    """單張圖片發布。多圖輪播 / 影片（Reels）需要不同的 container 流程，
    目前先支援單張圖片，之後可依 media 長度擴充。"""
    image_url = REPO_RAW_BASE + post["media"][0]
    caption = post.get("caption", "") + " " + " ".join(post.get("hashtags", []))

    container_resp = requests.post(
        f"https://graph.facebook.com/{GRAPH_API_VERSION}/{ig_user_id}/media",
        data={
            "image_url": image_url,
            "caption": caption.strip(),
            "access_token": token,
        },
        timeout=30,
    )
    container_resp.raise_for_status()
    container_id = container_resp.json()["id"]

    publish_resp = requests.post(
        f"https://graph.facebook.com/{GRAPH_API_VERSION}/{ig_user_id}/media_publish",
        data={"creation_id": container_id, "access_token": token},
        timeout=30,
    )
    publish_resp.raise_for_status()
    return publish_resp.json()


def main():
    token = os.environ.get("META_PAGE_TOKEN")
    ig_user_id = os.environ.get("IG_USER_ID")
    if not token or not ig_user_id:
        print("缺少 META_PAGE_TOKEN 或 IG_USER_ID 環境變數")
        sys.exit(1)

    calendar = load_yaml(CALENDAR_PATH, {"posts": []})
    archive = load_yaml(ARCHIVE_PATH, {"posts": []})

    post = find_todays_post(calendar)
    if not post:
        print("今天沒有 status=ready 的貼文，略過。")
        return

    try:
        result = publish_single_image(post, token, ig_user_id)
    except requests.HTTPError as e:
        print(f"發布失敗：{e}\n回應內容：{e.response.text if e.response else ''}")
        post["status"] = "failed"
        post["notes"] = str(e)
        save_yaml(CALENDAR_PATH, calendar)
        sys.exit(1)

    # 歸檔：從待發布移除，附上發布資訊後加進 archive
    calendar["posts"] = [p for p in calendar["posts"] if p is not post]
    post["status"] = "published"
    post["published_at"] = datetime.datetime.now().isoformat()
    post["ig_media_id"] = result.get("id")
    archive.setdefault("posts", []).append(post)

    save_yaml(CALENDAR_PATH, calendar)
    save_yaml(ARCHIVE_PATH, archive)
    print(f"發布成功並已歸檔：{post['id']}")


if __name__ == "__main__":
    main()
