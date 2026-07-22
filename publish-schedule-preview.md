# Aquar 發布次序與 YAML 草案預覽

**作者：Manus AI**  
**資料來源版本：** `4e7104b690534c1909b9cb4db1b4ad976196472c`

本草案以目前儲存庫的 `docs/publish-schedule-v2.json` 作為唯一排序來源，沿用既有的六週行銷漏斗，並將唯一延伸素材保留為 Week 7。此次只完成資料結構與次序設定，**沒有提交 GitHub、沒有觸發 Actions，也沒有連接或呼叫 Buffer**。[1] [2]

## 發布次序

| 週次 | 階段 | 主題 | 篇數 | 草案處理 |
|---:|---|---|---:|---|
| 1 | 破題喚醒 | Topic 1 微生態、Topic 2 pH 邊界 | 11 | 保留既有順序 |
| 2 | 痛點共感 | Topic 6 屏障修復 | 6 | 保留既有順序 |
| 3 | 科學論證 | Topic 3 分子滲透、Topic 5 成分潔癖 | 12 | 保留既有順序 |
| 4 | 品牌差異化 | Topic 8 數據與感性、Topic 9 挑剔權利 | 11 | 保留既有順序 |
| 5 | 生活整合 | Topic 4 生活儀式、Topic 7 微氣候 | 12 | 保留既有順序 |
| 6 | 長期陪伴 | Topic 10 從修復到維持 | 6 | 保留既有順序 |
| 7 | 延伸／可選 | 唯一未使用概念素材 | 1 | 預設不發布，須先改寫 |

核心內容共 **58 篇**，其中 56 篇為 `ready`、2 篇為 `ready_with_accepted_gap`；另有 1 篇延伸內容為 `needs_adaptation`，總計 **59 筆**。[1]

## YAML 安全設定

| 設定 | 草案值 | 意義 |
|---|---|---|
| `plan.publishing_enabled` | `false` | 全域禁止發布 |
| `plan.mode` | `order_only` | 目前只定義次序，不定義日期 |
| `plan.review_required` | `true` | 後續必須先核准 |
| `plan.timing.cadence` | `null` | 頻率尚未決定 |
| `plan.timing.start_at` | `null` | 起始日期尚未決定 |
| `delivery.strategy` | `undecided` | 尚未選擇 Buffer 直發或 IG 跨貼 |
| 每筆 `release.enabled` | `false` | 59 筆均未啟用 |
| 每筆 `release.approval` | `pending` | 59 筆均待確認 |

每筆項目均包含固定 ID、連續序號、週次、主題、內容路徑、文案檔、媒體清單、來源狀態與發布控制欄位。這使後續 GitHub Actions 可以只讀一份 YAML，避免同時依賴多個排程檔。

## 驗證結果

| 檢查項目 | 結果 |
|---|---|
| YAML 可解析 | 通過 |
| 項目數 | 59／59 |
| 序號 | 1–59 連續且無重複 |
| 內容、文案與圖片路徑 | 全部可解析 |
| 意外啟用發布 | 0 筆 |
| 驗證錯誤 | 0 |
| 警告 | 1：第 59 筆尚無可發布文案，符合 `needs_adaptation` 狀態 |

## 提交 GitHub 前仍需確認

| 決策 | 可選值 |
|---|---|
| 實際頻率 | 每日、每週二／五、或其他節奏 |
| 發布時間 | 例如 `09:00 Asia/Taipei` |
| 起始日期 | 尚未設定 |
| 發布路徑 | Buffer 直發 Facebook，或 Buffer 發 IG 後由 Meta 跨貼 |
| 缺 CTA 的兩篇 | 接受 3 頁版本，或發布前補圖 |
| Week 7 延伸素材 | 排除、改寫後保留，或只用於 Story／會員通路 |

> 建議下一步只先確認「頻率、時間、起始日期」三項，再產生具體 `publish_at`；仍維持發布停用，最後才另行確認是否提交到 GitHub。

## References

[1]: https://github.com/bioitrust0414-collab/aquar_9669/blob/4e7104b690534c1909b9cb4db1b4ad976196472c/docs/publish-schedule-v2.json "Aquar publish-schedule-v2.json"
[2]: https://github.com/bioitrust0414-collab/aquar_9669/blob/4e7104b690534c1909b9cb4db1b4ad976196472c/docs/replan-notes.md "Aquar 發布次序重新規劃說明"
