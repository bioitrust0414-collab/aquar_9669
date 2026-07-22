# Social Posts 自動發布系統

本資料夾是 **Aquar 69 Lab** 社群媒體自動發布的素材管理中心。
透過 GitHub Actions + Buffer API，實現圖文素材上傳後自動發布到 **Facebook** 與 **Instagram**。

---

## 資料夾結構

```
social-posts/
├── pending/          ← 待發布的素材放這裡
│   └── post-名稱/
│       ├── publish.json   ← 發布設定（必要）
│       ├── image1.jpg     ← 圖片（最多 5 張）
│       ├── image2.jpg
│       └── ...
└── published/        ← 發布成功後自動移入（勿手動修改）
```

---

## 使用方式

### Step 1：準備素材資料夾

在 `pending/` 下建立一個新資料夾（名稱建議用日期，例如 `2026-07-22-barrier-repair`），並放入：

- **圖片**：最多 5 張，支援 `.jpg`、`.png`
- **publish.json**：發布設定檔（格式見下方）

### Step 2：填寫 publish.json

```json
{
  "text": "貼文文案內容\n\n#hashtag1 #hashtag2 #hashtag3",
  "images": ["image1.jpg", "image2.jpg"]
}
```

| 欄位 | 說明 | 必填 |
|------|------|------|
| `text` | 貼文文案，支援換行（`\n`） | ✅ |
| `images` | 圖片檔名清單，順序即輪播順序 | 選填 |

### Step 3：Push 到 GitHub

將素材 Push 到 `main` 分支後，GitHub Actions 會自動觸發發布流程。

---

## 自動化流程說明

```
Push 素材到 pending/
        ↓
GitHub Actions 自動觸發
        ↓
Python 腳本讀取 publish.json
        ↓
透過 Buffer API 發布到 FB + IG
        ↓
發布成功 → 自動移至 published/
```

---

## 必要的 GitHub Secrets 設定

請至 GitHub 儲存庫 → Settings → Secrets and variables → Actions，新增以下兩個 Secrets：

| Secret 名稱 | 說明 | 取得方式 |
|------------|------|---------|
| `BUFFER_ACCESS_TOKEN` | Buffer 的**新版 personal API key**（Bearer token，**不是**舊版 OAuth access token） | Buffer 帳號 → Settings → 開發者 / API 頁面產生 personal API key |
| `BUFFER_CHANNEL_IDS` | 要發布的社群頻道 ID（JSON 陣列格式） | 透過 Buffer 新版 GraphQL API 查詢頻道 ID |

**BUFFER_CHANNEL_IDS 格式範例：**
```json
["CHANNEL_ID_FB", "CHANNEL_ID_IG"]
```

⚠️ 若使用舊版 OAuth access token，Buffer API 會回傳 `401 Access token is not valid`，貼文會一直卡在 `pending/` 無法發布。

---

## 注意事項

- 圖片必須是 `.jpg` 或 `.png` 格式
- 圖片數量上限為 **5 張**（IG 輪播限制）
- `published/` 資料夾由 GitHub Actions 自動管理，請勿手動修改
- 若發布失敗，素材會保留在 `pending/` 中，可查看 Actions 記錄排查原因
