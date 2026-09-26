import os
import json
import glob
from datetime import datetime, timedelta
import requests

# ----------------- 核心設定參數 -----------------
PENDING_DIR = "social-posts/pending"
PUBLISHED_DIR = "social-posts/published"
STATE_FILE = "docs/buffer-batch-state.json"
DEBUG_LOG = ".last-run-debug.log"

# 調整為：每批 9 篇，跨度 21 天（3週），配合每週一、三、五發布
BATCH_SIZE = 9
BATCH_INTERVAL_DAYS = 21

BUFFER_API_TOKEN = os.getenv("BUFFER_API_TOKEN")
BUFFER_PROFILE_IDS = os.getenv("BUFFER_PROFILE_IDS", "").split(",")

def log_debug(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}\n"
    print(log_msg.strip())
    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(log_msg)

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log_debug(f"讀取狀態檔錯誤: {e}")
    return {"last_batch_time": None, "published_count": 0}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def calculate_schedule_times(count):
    """
    計算接下來 21 天內，每週一、三、五的發布時間點
    確保時間點剛好對應 9 篇貼文
    """
    times = []
    current = datetime.utcnow()
    
    # 尋找未來符合一、三、五（1, 3, 5）的時間點
    candidate_days = []
    days_checked = 0
    while len(candidate_days) < count and days_checked < BATCH_INTERVAL_DAYS + 7:
        current += timedelta(days=1)
        # weekday(): 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
        if current.weekday() in [0, 2, 4]:  # 週一、週三、週五
            # 設定在當天台北時間早上 8:00 (即 UTC 0:00)，或保留當下執行的小時
            post_time = current.replace(hour=0, minute=5, second=0, microsecond=0)
            candidate_days.append(post_time)
        days_checked += 1
        
    return candidate_days[:count]

def post_to_buffer(post_content, scheduled_at):
    if not BUFFER_API_TOKEN or not BUFFER_PROFILE_IDS or not BUFFER_PROFILE_IDS[0]:
        log_debug("錯誤: 缺少 Buffer API Token 或 Profile IDs 設定")
        return False

    url = "https://api.bufferapp.com/1/updates/create.json"
    
    # 將時間轉換為 Unix Timestamp
    due_timestamp = int(scheduled_at.timestamp())
    
    success = True
    for profile_id in BUFFER_PROFILE_IDS:
        profile_id = profile_id.strip()
        if not profile_id:
            continue
            
        payload = {
            "access_token": BUFFER_API_TOKEN,
            "profile_ids[]": profile_id,
            "text": post_content,
            "scheduled_at": due_timestamp,
            "now": "false"
        }
        
        try:
            response = requests.post(url, data=payload)
            result = response.json()
            if result.get("success"):
                log_debug(f"成功排程至 Buffer (Profile: {profile_id}) 於時間: {scheduled_at}")
            else:
                log_debug(f"Buffer API 回傳失敗 (Profile: {profile_id}): {result}")
                success = False
        except Exception as e:
            log_debug(f"請求 Buffer API 發生例外錯誤: {e}")
            success = False
            
    return success

def main():
    log_debug("開始執行 Buffer 批次自動發布檢查...")
    
    # 檢查是否有待發布貼文
    os.makedirs(PENDING_DIR, exist_ok=True)
    os.makedirs(PUBLISHED_DIR, exist_ok=True)
    
    pending_files = sorted(glob.glob(os.path.join(PENDING_DIR, "*.json")))
    if not pending_files:
        log_debug("目前沒有待發布的貼文 (pending 目錄為空)。")
        return

    state = load_state()
    last_batch_time_str = state.get("last_batch_time")
    
    # 檢查是否達到 21 天的批次間隔（如果是手動工作流程觸發，可視需求略過時間間隔限制）
    if last_batch_time_str:
        last_batch_time = datetime.fromisoformat(last_batch_time_str)
        days_elapsed = (datetime.utcnow() - last_batch_time).days
        
        # 強制環境變數（例如手動觸發）可以突破時間限制，否則需要滿 21 天
        force_run = os.getenv("FORCE_RUN", "false").lower() == "true"
        if days_elapsed < BATCH_INTERVAL_DAYS and not force_run:
            log_debug(f"距上次發布僅經過 {days_elapsed} 天，尚未滿 {BATCH_INTERVAL_DAYS} 天週期。跳過執行。")
            return

    # 取出設定數量的貼文 (9 篇)
    batch_to_publish = pending_files[:BATCH_SIZE]
    log_debug(f"本次批次將處理 {len(batch_to_publish)} 篇貼文。")
    
    # 計算未來 21 天內對應的一、三、五發布時間點
    schedule_times = calculate_schedule_times(len(batch_to_publish))
    
    if len(schedule_times) < len(batch_to_publish):
        log_debug("警告: 計算出的可用發布時間點少於貼文數量。")

    success_count = 0
    for idx, file_path in enumerate(batch_to_publish):
        if idx >= len(schedule_times):
            break
            
        target_time = schedule_times[idx]
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                post_data = json.load(f)
                
            # 假設貼文內容欄位為 text 或 content
            content = post_data.get("text") or post_data.get("content")
            if not content:
                log_debug(f"檔案格式錯誤或缺少內文: {file_path}")
                continue
                
            # 發布至 Buffer
            if post_to_buffer(content, target_time):
                # 成功後移動到 published 目錄
                filename = os.path.basename(file_path)
                dest_path = os.path.join(PUBLISHED_DIR, filename)
                os.rename(file_path, dest_path)
                success_count += 1
                log_debug(f"已成功歸檔貼文: {filename} -> {dest_path}")
            else:
                log_debug(f"貼文排程失敗，保留在 pending: {file_path}")
                
        except Exception as e:
            log_debug(f"處理檔案 {file_path} 時發生錯誤: {e}")

    # 更新狀態
    if success_count > 0:
        state["last_batch_time"] = datetime.utcnow().isoformat()
        state["published_count"] = state.get("published_count", 0) + success_count
        save_state(state)
        log_debug(f"批次執行完畢，成功發布並排程 {success_count} 篇貼文。")
    else:
        log_debug("本次執行沒有成功發布任何貼文。")

if __name__ == "__main__":
    main()
