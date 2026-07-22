# momo_daily 協作規則

這份文件說明這個 repo 的資料結構與流程，給人和 AI agent 共同參考。

## 資料夾慣例

```
content/<character>/<YYYY-MM>/<YYYYMMDD>/檔案
```

例如：`content/momo/2026-06/20260618/momo_0618_photo1_morning.jpg`

新增素材時，請放進對應日期的資料夾再 push。`detect-new-content` workflow 會自動掃描，
幫還沒被排程表引用的檔案建立一筆 `draft` 項目。

## 排程表：schedule/content-calendar.yaml

每一筆貼文的欄位：

| 欄位 | 說明 |
|---|---|
| id | 唯一識別碼，慣例為 `<character>-<YYYYMMDD>` |
| character | 角色名稱（如 momo） |
| date | 預定發布日期 `YYYY-MM-DD` |
| platforms | 發布平台清單，目前僅支援 `instagram` |
| caption | 貼文文案 |
| hashtags | 標籤清單 |
| media | 素材相對路徑清單（相對於 repo 根目錄） |
| status | `draft`（待補文案）→ `ready`（可發布）→ 發布後自動搬到 archive.yaml |
| scheduled_time | 當天預定發布時間（目前僅供參考，實際觸發時間由 workflow 的 cron 決定） |

**只有 `status: ready` 的項目會被自動發布。** 新增的項目預設是 `draft`，
需要人工（或負責文案的 agent）填好 `caption` / `hashtags` 並改成 `ready`。

## 已發布紀錄：schedule/archive.yaml

由 `publish_to_meta.py` 自動寫入，包含發布時間與 IG media id，不需手動維護。

## 自動化流程

1. **新增素材** → push 到 `content/**` → `detect-new-content` workflow 自動建立 draft 項目
2. **人工補文案** → 把 draft 改成 ready
3. **每日 08:00（台灣時間）** → `publish` workflow 讀取當天 `ready` 的項目，發布到 Instagram，
   成功後自動歸檔到 archive.yaml

## 需要的 GitHub Secrets

- `META_PAGE_TOKEN`：Meta Graph API 的長效 Page/IG Access Token
- `IG_USER_ID`：Instagram Business 帳號的 user id

這兩個目前需手動透過 Meta for Developers 後台設定並取得。

## 目前限制 / 待擴充

- 目前只支援單張圖片發布，多圖輪播（carousel）與影片（Reels）需要另外實作 container 流程
- 只支援 Instagram，尚未加入 Facebook 發布邏輯
- Access Token 過期需要人工重新授權
