# Aquar 69 Lab — 女性健康科普內容管理系統

[![GitHub Actions](https://github.com/bioitrust0414-collab/aquar_9669/workflows/Publish%20to%20Social%20Media/badge.svg)](https://github.com/bioitrust0414-collab/aquar_9669/actions)
[![Repository Size](https://img.shields.io/github/repo-size/bioitrust0414-collab/aquar_9669)](https://github.com/bioitrust0414-collab/aquar_9669)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> 一個為 **Aquar 69 Lab** 女性健康科普品牌設計的內容管理與社群媒體自動發布系統。透過 GitHub + Buffer API，實現從內容製作、排程規劃到自動發布 Facebook 與 Instagram 的完整工作流程。

---

## 📋 目錄

- [內容規模](#-內容規模)
- [倉庫結構](#-倉庫結構)
- [10 大主題架構](#-10-大主題架構)
- [自動發布系統](#-自動發布系統)
- [已知問題與待修正事項](#️-已知問題與待修正事項)
- [快速開始](#-快速開始)
- [新增貼文](#-新增貼文)
- [排程配置說明](#-排程配置說明)
- [常見問題排查](#-常見問題排查)
- [內容缺口記錄](#-內容缺口記錄)

---

## 📊 內容規模

| 指標 | 數值 |
|------|------|
| 主要主題數 | 10 個 |
| 子主題數 | 48 個 |
| 核心文案篇數 | 58 篇 |
| 延伸項目 | 1 篇（`aquar-059`） |
| 圖卡總數 | 約 240 張（每子主題 5 張） |
| 待發布貼文 | 60 篇（`social-posts/pending/`） |
| 已發布貼文 | 60 篇（`social-posts/published/`） |
| 預計完整發布週期 | 約 17.7 週（每 21 天一批，一批 10 篇） |

> **注意**：`social-posts/published/` 中的貼文代表已成功移動到已發布資料夾，但**不代表全部已成功發布到 Buffer**。請以 Buffer 後台的實際發布數量為準。

---

## 📁 倉庫結構

```
aquar_9669/
├── .github/
│   └── workflows/
│       └── publish-social.yml      # GitHub Actions 工作流程（觸發邏輯在此）
├── content/                        # 原始內容與圖卡資料庫（唯讀參考）
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
├── social-posts/
│   ├── pending/                    # 待發布貼文（Push 後自動觸發發布）
│   ├── published/                  # 已處理的貼文（系統自動管理，勿手動修改）
│   ├── .last-run-debug.log         # 最近一次發布的詳細日誌
│   └── README.md                   # 貼文格式說明
├── docs/
│   ├── publish-schedule-v3-frequency.yaml  # 當前排程配置（⚠️ publishing_enabled: false）
│   ├── publish-schedule-v2.json            # v2 版本（行銷漏斗邏輯，參考用）
│   ├── publish-schedule.json               # v1 版本（原始順序，參考用）
│   ├── replan-notes.md                     # 排程調整說明與決策記錄
│   └── content-matrix-50-subtopics.doc     # 內容矩陣與主題清單
├── scripts/
│   ├── publish_to_buffer.py        # 主要發布腳本（Push 模式 + 排程模式）
│   └── publish_scheduled_post.py   # 排程專用腳本（備用）
├── tools/
│   ├── content-generator-week1.jsx # React 內容生成工具
│   └── content-generator-week3.jsx # React 內容生成工具
├── archive/                        # 舊版本與未使用素材（不納入發布排程）
│   ├── 2026-05-v1/
│   ├── kepu-topic10-extra/
│   └── topic10-unused-concept-draft/
└── README.md
```

---

## 🗂️ 10 大主題架構

內容依照**行銷漏斗邏輯**排序，從破題喚醒到長期陪伴：

| 階段 | 主題編號 | 主題名稱 | 子主題數 | 說明 |
|------|---------|---------|---------|------|
| 破題喚醒 | Topic 01 | 微生態動力學（Microbiome Dynamics） | 4 | 用反直覺數據打破迷思，搶奪注意力 |
| 破題喚醒 | Topic 02 | pH 邊界（pH Boundary） | 5 | 化學主權：pH 4.0 的生化法律 |
| 痛點共感 | Topic 06 | 屏障修復（Barrier Repair） | 5 | 越洗越敏感的惡性循環痛點 |
| 科學論證 | Topic 03 | 分子滲透（Molecular Permeation） | 5 | 扎實數據建立信任感 |
| 科學論證 | Topic 05 | 成分潔癖（Ingredient Purity） | 5 | 成分標籤閱讀與智慧消費 |
| 品牌差異化 | Topic 08 | 數據與感性（Data vs Emotion） | 5 | 建立「我們與其他品牌不同」的認同感 |
| 品牌差異化 | Topic 09 | 挑剔權利（Selective Rights） | 4 | 導入受眾自我認同（⚠️ 缺第 5 個子主題） |
| 生活整合 | Topic 04 | 生活儀式（Daily Ritual） | 5 | 把保養變成日常儀式 |
| 生活整合 | Topic 07 | 微氣候（Microclimate） | 5 | 台灣濕熱環境的身體微氣候管理 |
| 長期陪伴 | Topic 10 | 從修復到維持（Repair to Maintain） | 5 | 收束全案，導向長期訂閱與回購 |

---

## 🤖 自動發布系統

### 工作流程觸發條件

系統有三種觸發模式，行為各不相同：

| 觸發方式 | 條件 | 發布數量 | 適用場景 |
|---------|------|---------|---------|
| **Push 觸發** | 有新檔案 push 到 `main` 分支的 `social-posts/pending/**` | **全部** pending 貼文 | 緊急或批次發布 |
| **排程觸發** | 每天 00:05 UTC 檢查一次，若距上次批次已滿 21 天則觸發 | 一批 **10 篇**（不足 10 篇時發剩餘全部） | 穩定節奏的批次自動發布 |
| **手動觸發** | GitHub Actions → Run workflow | 立即觸發一批 10 篇（略過 21 天等待） | 手動補發、測試，或提前開始下一批 |

> ⚠️ **重要**：Push 觸發模式會一次發布**所有** pending 資料夾中的貼文，容易造成社群媒體洗版，請謹慎使用。此觸發僅限 `main` 分支（其他分支的 push 不會觸發）。

### 發布腳本邏輯：21 天批次制

`scripts/publish_to_buffer.py` 在排程模式下維護一個狀態檔 `docs/buffer-batch-state.json`（記錄 `last_batch_at`），每天執行時計算距離上次批次是否已滿 21 天：

- **未滿 21 天**：不做任何事，直接結束（避免每天都重覆判斷造成混淆，log 會標示還差幾天）。
- **已滿 21 天（或第一次執行、或手動觸發強制略過等待）**：從 `pending/` 依資料夾名稱排序取出接下來 **10 篇**，各自指定一個在未來 21 天內平均分散的發布時間（`scheduled_at`），一次性交給 Buffer 的排程功能（`customScheduled` 模式），由 Buffer 自己在指定時間陸續真正發文——腳本本身不會短時間內對 Buffer 連續打 10 次「立即發布」的請求，避免撞到 Buffer 的速率限制。
- 這批 10 篇只要有 **至少 1 篇** 成功送進 Buffer，就會把 `last_batch_at` 更新為本次執行時間，21 天倒數重新開始；如果整批 10 篇全部失敗（例如 Buffer 短暫中斷），則不更新狀態，隔天會自動整批重試。

58 篇核心內容 ÷ 10 篇/批 ≈ 6 批，每批間隔 21 天，完整跑完（含最後一批的分散發文）約 124 天（約 17.7 週 / 4.1 個月）。

---

## ⚠️ 已知問題與待修正事項

### 問題 1：published/ 資料夾與 Buffer 實際發布數量不一致

`social-posts/published/` 中有 60 篇，但 Buffer 後台顯示的數量可能不同。這是因為腳本在發布成功後才移動資料夾，但 Buffer 的排程佇列與實際發布時間不同。**請以 Buffer 後台為準**。

---

## 🚀 快速開始

### 1. 環境設定

在 GitHub 倉庫設定中新增以下 Secrets（Settings → Secrets and variables → Actions）：

| Secret 名稱 | 說明 | 取得方式 |
|------------|------|---------|
| `BUFFER_ACCESS_TOKEN` | Buffer personal API key（Bearer token） | Buffer → Settings → API |
| `BUFFER_CHANNEL_IDS` | 要發布的社群頻道 ID（JSON 陣列） | Buffer GraphQL API 查詢 |

**`BUFFER_CHANNEL_IDS` 格式範例：**
```json
["6a605f5ee2638b94d7b1e3fe", "6a605f5ee2638b94d7b1e3ff"]
```

> ⚠️ 必須使用 Buffer **新版** personal API key（Bearer token），不是舊版 OAuth access token。舊版 token 會導致 `401 Unauthorized` 錯誤。

### 2. 驗證設定

手動觸發一次 GitHub Actions 確認設定正確：
1. 進入 **Actions** 標籤
2. 選擇 **Publish to Social Media**
3. 點擊 **Run workflow**
4. 查看執行結果與 `social-posts/.last-run-debug.log`

---

## 📝 新增貼文

在 `social-posts/pending/` 下建立新資料夾：

```
social-posts/pending/aquar-XXX-topic-name/
├── publish.json    # 貼文配置（必填）
├── card-1.jpg      # 圖片（選填，最多 5 張）
└── card-2.jpg
```

**`publish.json` 格式：**
```json
{
  "text": "貼文文案內容...\n\n#hashtag1 #hashtag2",
  "images": ["card-1.jpg", "card-2.jpg"],
  "scheduled_at": null
}
```

Push 到 GitHub 後，GitHub Actions 會自動觸發並發布所有 pending 貼文。

---

## ⚙️ 排程配置說明

目前有三個版本的排程配置，均存放於 `docs/` 資料夾：

| 檔案 | 版本 | 邏輯 | 狀態 |
|------|------|------|------|
| `publish-schedule.json` | v1 | 依話題編號 1→10 依序發布 | 參考用 |
| `publish-schedule-v2.json` | v2 | 行銷漏斗邏輯（破題→痛點→科學→差異化→生活→長期） | 參考用 |
| `publish-schedule-v3-frequency.yaml` | v3（當前） | 頻率優先輪替制（每輪各話題各出一篇） | `publishing_enabled: true`（規劃參考，實際發布順序由 `pending/` 資料夾名稱排序決定，程式不會讀取此檔） |

**實際排程節奏（由 `scripts/publish_to_buffer.py` 控制，非此處的 v3 檔案）：**
- 每 21 天一批，一批 10 篇，58 篇核心內容約 6 批、124 天（約 17.7 週 / 4.1 個月）發完
- 前 26 篇約 3 批、60 天（約 8.6 週）

**修改批次參數（`scripts/publish_to_buffer.py`）：**
```python
BATCH_INTERVAL_DAYS = 21  # 幾天一批
BATCH_SIZE = 10           # 一批幾篇
```

**修改每日檢查時間（`publish-social.yml`）：**
```yaml
schedule:
  # 目前：每天 UTC 00:05（台北 08:05）檢查一次是否該觸發批次
  - cron: '5 0 * * *'
```

---

## 🔧 常見問題排查

**401 Unauthorized**
使用的是舊版 OAuth token，請改用新版 personal API key（Bearer token）。

**Channel not found**
`BUFFER_CHANNEL_IDS` 中的頻道 ID 無效，請透過 Buffer GraphQL API 重新查詢。

**圖片無法顯示**
腳本使用 `raw.githubusercontent.com` URL 提供圖片，倉庫必須保持**公開（Public）**。若改為私有倉庫，圖片 URL 將失效。

**貼文卡在 pending**
查看 `social-posts/.last-run-debug.log` 確認錯誤原因，修復後手動觸發重新發布。

**排程模式一直沒有動作**
檢查 `docs/buffer-batch-state.json` 的 `last_batch_at`：只要距離現在不滿 21 天就是正常現象（每天執行的 log 會標示還差幾天）。若要立即觸發下一批，不想等 21 天，可手動執行 GitHub Actions（`workflow_dispatch` 會略過等待直接發一批）。

---

## 📋 內容缺口記錄

對照 `docs/content-matrix-50-subtopics.doc` 原始矩陣，目前有以下缺口：

| 主題 | 缺少項目 | 說明 | 處理方式 |
|------|---------|------|---------|
| Topic 09（挑剔權利） | 第 5 個子主題 | 矩陣原題：「身體的資產：妳的身體是妳最珍貴的資產」 | 替代素材 `archive/topic10-unused-concept-draft/investment-mockup-a` 視覺風格與品牌 SOP 不同調，維持獨立延伸項目，不補位成 `kepu-9.5` |
| Topic 10（從修復到維持） | 第 3 個子主題 | 矩陣原題：「長期主義：為什麼身體的健康與平衡需要時間與持續的投入」 | 只有文案草稿 `archive/kepu-topic10-extra/long-termism.docx`，缺圖卡，暫不納入排程 |

---

## 📚 相關文件

- [`social-posts/README.md`](social-posts/README.md)：貼文格式與管理說明
- [`docs/replan-notes.md`](docs/replan-notes.md)：排程調整說明與決策記錄
- [`docs/publish-schedule-v3-frequency.yaml`](docs/publish-schedule-v3-frequency.yaml)：當前發布排程配置
- [`.github/workflows/publish-social.yml`](.github/workflows/publish-social.yml)：GitHub Actions 工作流程

---

## 📄 許可證

本專案採用 MIT 許可證。詳見 [LICENSE](LICENSE) 文件。

---

**最後更新**：2026 年 8 月 3 日
**維護者**：Aquar 69 Lab 團隊
**倉庫連結**：[https://github.com/bioitrust0414-collab/aquar_9669](https://github.com/bioitrust0414-collab/aquar_9669)
