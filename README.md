# Aquar 69 Lab — 社群媒體自動發布系統

[![GitHub Actions](https://github.com/bioitrust0414-collab/aquar_9669/workflows/Publish%20to%20Social%20Media/badge.svg)](https://github.com/bioitrust0414-collab/aquar_9669/actions)[![Repository Size](https://img.shields.io/github/repo-size/bioitrust0414-collab/aquar_9669)](https://github.com/bioitrust0414-collab/aquar_9669)[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

一個為 **Aquar 69 Lab** 女性健康科普品牌設計的全自動社群媒體內容管理與發布系統。透過 GitHub Actions + Buffer API，實現從內容製作、排程規劃到自動發布 Facebook 與 Instagram 的完整工作流程。

## 🎯 核心特性

- **自動化發布**：Push 素材到 `social-posts/pending/` 後自動發布到 Facebook 與 Instagram

- **排程發布**：每週二至五自動執行，每次發布一篇，避免手動操作

- **智能排程**：支援三種觸發模式（Push、排程、手動），靈活適應不同場景

- **系統化內容**：58 篇核心內容 + 1 篇延伸項目，涵蓋 10 大女性健康主題

- **行銷漏斗邏輯**：從破題喚醒、痛點共感、科學論證到長期陪伴的完整說服路徑

- **圖文並茂**：每篇貼文支援最多 5 張高質量圖片，支援 Instagram 輪播

- **詳細日誌**：完整的發布日誌與錯誤追蹤，便於排查問題

## 📁 倉庫結構

```
aquar_9669/
├── social-posts/              # 社群貼文素材管理中心
│   ├── pending/               # 待發布的貼文（Push 後自動發布）
│   ├── published/             # 已發布的貼文（自動管理，勿手動修改）
│   └── README.md              # 詳細的貼文管理說明
├── content/                   # 原始內容與圖卡資料庫
│   ├── topic-01-microbiome-dynamics/
│   ├── topic-02-ph-boundary/
│   ├── topic-03-molecular-permeation/
│   ├── topic-04-daily-ritual/
│   ├── topic-05-ingredient-purity/
│   ├── topic-06-barrier-repair/
│   ├── topic-07-microclimate/
│   ├── topic-08-data-vs-emotion/
│   ├── topic-09-selective-rights/
│   └── topic-10-repair-to-maintain/
├── docs/                      # 規劃文件與排程配置
│   ├── publish-schedule-v3-frequency.yaml  # 當前使用的發布排程
│   ├── publish-schedule-v2.json            # v2 版本（行銷漏斗邏輯）
│   ├── publish-schedule.json               # v1 版本（參考用）
│   ├── replan-notes.md                     # 排程調整說明
│   └── content-matrix-50-subtopics.doc     # 內容矩陣與主題清單
├── scripts/                   # 自動化發布腳本
│   ├── publish_to_buffer.py               # 通用發布腳本（支援 Push 與排程模式）
│   └── publish_scheduled_post.py           # 排程專用腳本（每次發布一篇）
├── tools/                     # 輔助工具
│   ├── content-generator-week1.jsx        # React 內容生成器
│   └── content-generator-week3.jsx        # React 內容生成器
├── archive/                   # 舊版本與未使用的素材
│   ├── 2026-05-v1/            # 第一版內容備份
│   ├── kepu-topic10-extra/    # 延伸文案
│   └── topic10-unused-concept-draft/      # 未使用的概念草稿
├── .github/
│   └── workflows/
│       └── publish-social.yml # GitHub Actions 工作流程配置
└── README.md                  # 本文件
```

## 🚀 快速開始

### 1. 環境設定

#### GitHub Secrets 配置

在倉庫設定中新增以下 Secrets（Settings → Secrets and variables → Actions）：

| Secret 名稱 | 說明 | 取得方式 |
| --- | --- | --- |
| `BUFFER_ACCESS_TOKEN` | Buffer 新版 personal API key（Bearer token） | Buffer 帳號 → Settings → 開發者 / API 頁面產生 |
| `BUFFER_CHANNEL_IDS` | 要發布的社群頻道 ID（JSON 陣列格式） | 透過 Buffer GraphQL API 查詢 |

**BUFFER_CHANNEL_IDS 格式範例**：

```json
["6a605f5ee2638b94d7b1e3fe", "6a605f5ee2638b94d7b1e3ff"]
```

⚠️ **重要**：使用 Buffer 新版 personal API key（Bearer token），不是舊版 OAuth access token。舊版 token 會導致 `401 Unauthorized` 錯誤。

#### Python 依賴

該系統使用 Python 3.11，主要依賴為：

```bash
pip install requests pillow
```

- `requests`：與 Buffer API 通信

- `pillow`：圖片尺寸提取（可選，若無則跳過尺寸提取）

### 2. 新增待發布貼文

在 `social-posts/pending/` 下建立新資料夾，並準備以下檔案：

```
social-posts/pending/aquar-001-microbiome-dynamics/
├── publish.json          # 發布配置（必填）
├── hook.jpg              # 圖片 1（可選，最多 5 張）
├── transition.jpg        # 圖片 2
└── data.jpg              # 圖片 3
```

#### publish.json 格式

```json
{
  "text": "【防線的物理學】為什麼精準的「邊界感」，是你/妳系統穩定的前提？\n\n你/妳或許也曾感受過那種莫名的「系統雜訊」……\n\n#生理主權 #微生態管理 #智性生活",
  "images": ["hook.jpg", "transition.jpg", "data.jpg"],
  "scheduled_at": "2026-07-28T08:15:00+08:00"
}
```

| 欄位 | 說明 | 必填 | 格式 |
| --- | --- | --- | --- |
| `text` | 貼文文案，支援換行（`\n`） | ✅ | 字串 |
| `images` | 圖片檔名清單，順序即輪播順序 | 選填 | 陣列 |
| `scheduled_at` | 排程發布時間（ISO 8601 格式） | 選填 | 字串 |

### 3. Push 到 GitHub 並自動發布

```bash
git add social-posts/pending/aquar-001-microbiome-dynamics/
git commit -m "Add aquar-001 post: microbiome dynamics"
git push origin main
```

系統會自動觸發 GitHub Actions，將貼文發布到 Facebook 與 Instagram。發布成功後，資料夾會自動移至 `social-posts/published/`。

## 📅 發布排程

### 觸發方式

該系統支援三種觸發方式：

| 觸發方式 | 條件 | 發布模式 | 說明 |
| --- | --- | --- | --- |
| **Push 觸發** | Push 到 `social-posts/pending/` | 發布所有待發布貼文 | 適合批量上傳內容 |
| **排程觸發** | 每週二至五 UTC 00:05（台北時間 08:05） | 發布一篇（aquar-023+） | 自動定時發布，避免手動操作 |
| **手動觸發** | GitHub Actions 介面 → Run workflow | 根據 PUBLISH_MODE 決定 | 應急發布或測試用 |

### 排程模式說明

在排程模式下，系統會自動跳過 aquar-001～022（已排程的早期內容），僅發布 aquar-023 及之後的議題。這樣設計的目的是避免重複發布已排程的內容。

**排程時間表**（每週）：

| 日期 | 時間（UTC） | 時間（台北） | 發布數量 |
| --- | --- | --- | --- |
| 週二 | 00:05 | 08:05 | 1 篇 |
| 週三 | 00:05 | 08:05 | 1 篇 |
| 週四 | 00:05 | 08:05 | 1 篇 |
| 週五 | 00:05 | 08:05 | 1 篇 |

### 發布順序（v3 版本）

當前使用的 v3 排程採用**頻率優先邏輯**，透過輪替制避免同一話題連續出現。發布順序遵循以下邏輯：

1. **第一輪**：各話題主貼文（aquar-001, aquar-006, aquar-012, aquar-018, aquar-024, aquar-030, aquar-036, aquar-041, aquar-047, aquar-053）

1. **第二輪**：各話題 kepu 1（aquar-002, aquar-007, aquar-013, aquar-019, aquar-025, aquar-031, aquar-037, aquar-042, aquar-048, aquar-054）

1. **第三輪**：各話題 kepu 2

1. **以此類推**

預計 58 篇核心內容 + 1 篇延伸共需約 14.75 週（約 3.5 個月）發布完成。

詳細排程配置見 [`docs/publish-schedule-v3-frequency.yaml`](docs/publish-schedule-v3-frequency.yaml)。

## 📊 內容架構

### 10 大主題與行銷漏斗

倉庫管理的內容遵循行銷漏斗邏輯，共分為 6 個階段：

| 階段 | 主題 | 目標 | 內容數量 |
| --- | --- | --- | --- |
| 1️⃣ 破題喚醒 | Topic 1-2 | 用反直覺數據與迷思打破做鉤子，搶奪注意力 | 10 篇 |
| 2️⃣ 痛點共感 | Topic 6 | 提前處理「越洗越敏感」的惡性循環痛點，建立同理心 | 6 篇 |
| 3️⃣ 科學論證 | Topic 3, 5 | 用扎實數據建立信任感，是說服的核心 | 12 篇 |
| 4️⃣ 品牌差異化 | Topic 8-9 | 建立「我們與其他品牌不同」的認同感 | 12 篇 |
| 5️⃣ 生活整合 | Topic 4, 7 | 把保養變成日常儀式，搭配台灣季節時事 | 12 篇 |
| 6️⃣ 長期陪伴收尾 | Topic 10 | 收束全案，導向長期訂閱與回購 | 6 篇 |

### 內容組成

每個主題包含：

- **主貼文**（1 篇）：話題概述與核心訊息

- **Kepu 科普系列**（5 篇）：深度探討與實踐指南

例如 Topic 1（微生態動力學）包含：

1. `aquar-001-microbiome-dynamics`：主貼文

1. `aquar-002-kepu-1.1-good-bad-bacteria`：Kepu 1 - 好菌與壞菌

1. `aquar-003-kepu-1.2-sterile-myth`：Kepu 2 - 無菌迷思

1. `aquar-004-kepu-1.3-molecular-permeation`：Kepu 3 - 分子滲透

1. `aquar-005-kepu-1.4-daily-habits`：Kepu 4 - 日常習慣

1. `aquar-006-kepu-1.5-...`：Kepu 5 - 其他主題

## 🔧 工作流程詳解

### GitHub Actions 工作流程

工作流程檔案位於 [`.github/workflows/publish-social.yml`](.github/workflows/publish-social.yml)，執行步驟如下：

1. **檢出代碼**：使用 `actions/checkout@v3` 檢出倉庫

1. **設定 Python**：安裝 Python 3.11

1. **安裝依賴**：執行 `pip install requests`

1. **決策發布策略**：根據觸發事件決定是 Push 模式還是排程模式

1. **執行發布腳本**：執行 `scripts/publish_to_buffer.py`

1. **提交變更**：將發布成功的貼文移至 `published/` 並提交回倉庫

### Python 發布腳本

#### publish_to_buffer.py（通用腳本）

該腳本支援 Push 模式與排程模式，核心功能包括：

- **讀取待發布貼文**：掃描 `social-posts/pending/` 中的所有資料夾

- **提取圖片尺寸**：使用 PIL 提取本地圖片的寬高，確保 Buffer 正確顯示

- **構建資產物件**：將圖片 URL 與尺寸組合成 Buffer API 所需格式

- **發布到 Buffer**：透過 GraphQL API 的 `createPost` mutation 發布貼文

- **移動已發布貼文**：成功發布後移至 `social-posts/published/`

**執行流程**：

```
讀取 publish.json
  ↓
提取圖片尺寸
  ↓
構建 GraphQL mutation
  ↓
發送到 Buffer API
  ↓
檢查回應狀態
  ↓
成功 → 移至 published/
失敗 → 保留在 pending/，記錄錯誤日誌
```

#### publish_scheduled_post.py（排程專用）

該腳本用於排程模式，每次執行僅發布一篇，防止重複發布。與通用腳本的主要差異為：

- 每次執行只發布 `pending/` 中的第一篇貼文

- 記錄詳細的時間戳與執行日誌

- 支援 `scheduled_at` 欄位，允許指定發布時間

## 📝 日誌與故障排查

### 發布日誌位置

發布日誌自動記錄在 `social-posts/.last-run-debug.log`，包含以下資訊：

- 發布時間與倉庫資訊

- 待發布貼文清單

- 各頻道的發布結果（成功或失敗）

- 圖片尺寸資訊（若 PIL 可用）

- 錯誤訊息與 GraphQL 回應

### 常見問題排查

#### 問題 1：401 Unauthorized

**原因**：Buffer API token 無效或過期

**解決方案**：

1. 檢查 GitHub Secrets 中的 `BUFFER_ACCESS_TOKEN` 是否正確

1. 確保使用的是新版 personal API key，而非舊版 OAuth access token

1. 從 Buffer 帳號重新生成 API key

#### 問題 2：Channel not found

**原因**：頻道 ID 無效或已刪除

**解決方案**：

1. 驗證 `BUFFER_CHANNEL_IDS` 中的頻道 ID 是否正確

1. 透過 Buffer GraphQL API 查詢當前可用的頻道 ID

1. 更新 GitHub Secrets 中的 `BUFFER_CHANNEL_IDS`

#### 問題 3：GraphQL validation error

**原因**：API schema 不匹配，可能是 Buffer API 版本更新

**解決方案**：

1. 查看 `.last-run-debug.log` 中的詳細錯誤訊息

1. 檢查 Buffer API 文件，確認 `CreatePostInput` 的當前 schema

1. 更新 `scripts/publish_to_buffer.py` 中的 GraphQL mutation

#### 問題 4：圖片無法顯示

**原因**：圖片 URL 無效或倉庫變為私有

**解決方案**：

1. 確保倉庫為公開（Public）

1. 驗證 `raw.githubusercontent.com` URL 是否可正常存取

1. 檢查圖片檔案是否存在且格式正確（`.jpg` 或 `.png`）

#### 問題 5：貼文卡在 pending

**原因**：發布失敗，素材未移至 `published/`

**解決方案**：

1. 查看 `.last-run-debug.log` 中的錯誤訊息

1. 根據錯誤類型進行相應排查（見上方常見問題）

1. 修復問題後，可手動觸發 GitHub Actions 重新發布

### 手動觸發發布

若需要手動觸發發布流程（例如重新發布失敗的貼文），可在 GitHub 倉庫中：

1. 進入 **Actions** 標籤

1. 選擇 **Publish to Social Media** 工作流程

1. 點擊 **Run workflow** → **Run workflow**

## 📚 進階使用

### 自訂排程時間

若需要修改排程時間（目前為每週二至五 UTC 00:05），編輯 `.github/workflows/publish-social.yml`：

```yaml
schedule:
  # 修改 cron 表達式
  - cron: '5 0 * * 2,3,4,5'  # 目前設定
  # 例如改為每天 08:00 台北時間
  # - cron: '0 0 * * *'  # 每天 UTC 00:00（台北時間 08:00）
```

Cron 表達式格式：`分 時 日 月 週`

- `0 0 * * *`：每天 UTC 00:00

- `0 8 * * 1-5`：週一至五 UTC 08:00

- `0 */6 * * *`：每 6 小時

### 修改發布頻率

若需要修改每次發布的貼文數量，編輯 `scripts/publish_to_buffer.py` 中的 `main()` 函數：

```python
if publish_mode == "scheduled":
    # 修改此行以改變每次發布的貼文數量
    filtered_dirs = [d for d in post_dirs if any(f"aquar-{i:03d}" in d.name for i in range(23, 100))]
    if filtered_dirs:
        post_dirs = filtered_dirs[:1]  # 改為 [:2] 表示每次發布 2 篇
```

### 擴展至其他社群平台

若需要擴展至 TikTok、LinkedIn 等其他平台，需要：

1. 在 Buffer 中連接新的社群頻道

1. 將新頻道 ID 新增至 `BUFFER_CHANNEL_IDS`

1. 若平台有特殊格式要求，可在 `publish_to_buffer.py` 中新增平台特定的內容轉換邏輯

## 🤝 貢獻指南

### 新增內容

1. 在 `content/topic-XX-*/` 下建立新的內容資料夾

1. 準備文案與圖片

1. 在 `social-posts/pending/` 下建立對應的貼文資料夾

1. 填寫 `publish.json` 配置

1. Push 到 GitHub，系統會自動發布

### 報告問題

若發現 bug 或有改善建議，請在 GitHub Issues 中提出。

### 改進工作流程

若要改進自動化流程，可：

1. 修改 `.github/workflows/publish-social.yml`

1. 更新 `scripts/publish_to_buffer.py` 或 `scripts/publish_scheduled_post.py`

1. 在 Pull Request 中詳細說明改進內容

1. 等待審核後合併

## 📖 相關文件

- [`social-posts/README.md`](social-posts/README.md)：詳細的貼文管理說明

- [`docs/replan-notes.md`](docs/replan-notes.md)：排程調整與內容策略說明

- [`docs/publish-schedule-v3-frequency.yaml`](docs/publish-schedule-v3-frequency.yaml)：當前發布排程配置

- [`.github/workflows/publish-social.yml`](.github/workflows/publish-social.yml)：GitHub Actions 工作流程

## 📊 統計資訊

| 指標 | 數值 |
| --- | --- |
| 倉庫大小 | 760 MB |
| Git 提交數 | 114 次 |
| 圖片數量 | 902 張 |
| 配置檔案 | 122 個 |
| 核心內容 | 58 篇 + 1 篇延伸 |
| 主題數 | 10 個 |
| 待發布貼文 | 60 篇 |
| 已發布貼文 | 60 篇 |

## 📄 許可證

本專案採用 MIT 許可證。詳見 [LICENSE](LICENSE) 文件。

## 📞 聯絡方式

如有任何問題或建議，請透過以下方式聯絡：

- **GitHub Issues**：[https://github.com/bioitrust0414-collab/aquar_9669/issues](https://github.com/bioitrust0414-collab/aquar_9669/issues)

- **GitHub Discussions**：[https://github.com/bioitrust0414-collab/aquar_9669/discussions](https://github.com/bioitrust0414-collab/aquar_9669/discussions)

---

**最後更新**：2026 年 7 月 27 日**維護者**：Aquar 69 Lab 團隊**倉庫連結**：[https://github.com/bioitrust0414-collab/aquar_9669](https://github.com/bioitrust0414-collab/aquar_9669)
