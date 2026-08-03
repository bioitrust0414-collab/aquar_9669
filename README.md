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
| 預計完整發布週期 | 約 14.75 週（每週 4 篇） |

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
| **Push 觸發** | 有新檔案 push 到 `social-posts/pending/**` | **全部** pending 貼文 | 緊急或批次發布 |
| **排程觸發** | 每週二至五 00:05 UTC（台北 08:05） | 每次 **1 篇** | 穩定節奏的自動發布 |
| **手動觸發** | GitHub Actions → Run workflow | **全部** pending 貼文 | 手動補發或測試 |

> ⚠️ **重要**：Push 觸發模式會一次發布**所有** pending 資料夾中的貼文，容易造成社群媒體洗版。請謹慎使用。

### 發布腳本邏輯

排程模式下，腳本目前**硬編碼**為只發布 `aquar-023` 及之後的議題：

```python
# 在排程模式下，只發布 aquar-023 及之後的議題（跳過已排程的 aquar-001～022）
filtered_dirs = [d for d in post_dirs if any(f"aquar-{i:03d}" in d.name for i in range(23, 100))]
if filtered_dirs:
    post_dirs = filtered_dirs[:1]  # 每次只發布一篇
```

這意味著 `aquar-001` 到 `aquar-022` 在排程模式下**不會被發布**，只能透過 Push 或手動觸發。

---

## ⚠️ 已知問題與待修正事項

### 問題 1：排程配置標記為禁用

`docs/publish-schedule-v3-frequency.yaml` 中設定了：

```yaml
publishing_enabled: false
```

這個欄位目前**不影響** GitHub Actions 的實際執行（GitHub Actions 的觸發由 `.github/workflows/publish-social.yml` 控制），但代表排程策略尚未正式確認。建議確認發布策略後，將此欄位改為 `true` 以反映實際狀態。

### 問題 2：排程模式的硬編碼起始點

`scripts/publish_to_buffer.py` 中的排程模式硬編碼從 `aquar-023` 開始，`aquar-001` 到 `aquar-022` 只能透過 Push 觸發發布。

**建議修改**：改為動態讀取 pending 資料夾中的第一篇：

```python
# 建議改為：
if publish_mode == "scheduled":
    if post_dirs:
        post_dirs = post_dirs[:1]  # 每次只發布第一篇（動態，不硬編碼）
```

### 問題 3：Push 觸發會一次發布所有貼文

Push 模式會發布 pending 資料夾中的**所有**貼文，容易造成社群媒體洗版。建議評估是否需要限制 Push 模式的發布數量，或改為只在手動觸發時才批次發布。

### 問題 4：published/ 資料夾與 Buffer 實際發布數量不一致

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
| `publish-schedule-v3-frequency.yaml` | v3（當前） | 頻率優先輪替制（每輪各話題各出一篇） | ⚠️ `publishing_enabled: false` |

**v3 排程的發布節奏：**
- 每週 4 篇，58 篇核心內容約 14.75 週（約 3.5 個月）發完
- 前 26 篇（約 6.5 週）為 `phase_1`，其餘為 `phase_2`

**修改排程時間（`publish-social.yml`）：**
```yaml
schedule:
  # 目前：每週二至五 UTC 00:05（台北 08:05）
  - cron: '5 0 * * 2,3,4,5'
  # 範例：每天 UTC 00:00（台北 08:00）
  # - cron: '0 0 * * *'
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

**排程模式無法發布 aquar-001 到 aquar-022**
這是腳本的已知限制（硬編碼從 aquar-023 開始），需手動觸發或 Push 觸發才能發布這些貼文。詳見[已知問題](#️-已知問題與待修正事項)。

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
