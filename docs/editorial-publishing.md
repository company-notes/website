# Company Notes｜作者手寫文章的編輯與發布流程

這份規則適用於作者提供繁體中文親筆稿，請 AI 協助小幅精修、翻譯、排版，並直接發表在 Company Notes 的情況。這是往後的預設工作方式；除非作者特別要求，無須每篇重新交代。

## 1. 最重要的原則：作者保有自己的聲音

- **以作者原文為主，不要代寫、重寫或重新安排觀點。**保留第一人稱、口語、玩笑、吐槽、情緒、親身經驗，以及原本的段落與論述順序。
- 只做**小精修**：斷句、標點、錯別字、全形／半形空格、專有名詞大小寫（如 AI、Grok Bot、GitHub、Markdown、Google Drive）、明顯重複／誤貼字句、Markdown 排版。
- 作者未指定標題時，可以擬一個貼近原意、不聳動的標題；SEO description 也只能忠實摘要，不能憑空補事實。
- 不把作者的經驗改寫成 AI 的一般論述，不加入沒有提供的數字、成功案例或沒有測過的承諾。若技術有實際執行過、修正版尚未實測，要保留這個區別；不要自行聲稱驗證完成。
- 有明確 GitHub repo 連結時，直接補到原文的位置，不留下占位文字。作者原本已寫的提醒、限制、使用方式與結語應完整保留。
- 不要擅自把「備份完整性」改成「依資料敏感度篩選內容」；備份範圍、取得限制與資料儲存責任應分開敘述，尊重作者的實際做法。

## 2. 同時發佈三語系，語意一致、用語在地化

同一篇文章在下列三個路徑使用**相同檔名、date、slug、分類、標籤、精選設定、封面、發表狀態**：

- `content/zh-hant/blog/posts/YYYY-MM-DD-slug.md`：繁體中文是作者原稿，僅小精修，保留台灣用語。
- `content/en/blog/posts/YYYY-MM-DD-slug.md`：英文譯文自然、忠實，保留作者口吻和玩笑，不加料、不刪減關鍵內容。
- `content/zh-hans/blog/posts/YYYY-MM-DD-slug.md`：使用中國大陸讀者習慣的簡體中文**重新翻譯與在地化**，不是機械轉換字形。例如「檔案→文件」、「資料夾→文件夾」、「腳本→脚本」、「助理→助手」、「資料庫→数据库」、「工作區→工作空间」、「程式碼→代码」、「備份驗證→备份校验」。保留品牌與專案名稱的原文拼寫。

三個版本都要保留**全部內容、所有小標、資訊、連結、警語、作者結論**；語意不可因翻譯而變強、變弱或增加未經證實的說法。

## 3. 發稿 metadata 與首頁規則

每篇以 YAML frontmatter 提供 `title`、`date`、`slug`、`description`、`categories`（只能選一個：`Field Notes`／`Playbooks`／`Toolkit`）、`tags`、`featured_image`、`status`。可用 `featured: true` 和 `featured_order` 排精選順位。

- 作者提供的真實第一手文章，且明確要求**正式發佈**，用 `status: published`。
- AI 先寫、尚待人工審稿的稿件用 `status: review`（**公開可見**，有 AI 初稿告示與 noindex）。
- 不應出現在公開網站的內容才用 `draft: true`。
- 適當位置放 `<!-- more -->` 決定 Blog 摘要，勿打亂文章敘述。
- 新文章優先在既有 `shared/assets/covers/` 找適用封面，不為了填滿版面虛構內容或事例。必要時另加真實主題封面。
- 不要手動修改 `content/<locale>/index.md`、`playbooks/index.md` 或 `toolkit/index.md`；`scripts/render_home.py` 會依 frontmatter 自動產生。不要手動修改文章 slug 造成已公開網址失效。

## 4. 正式發佈步驟

1. 取得作者繁體中文原文，最小限度整理標點／斷句／大小寫及明顯重複字句；其他地方不擅改。
2. 按繁中確認的同一份內容完成英文與**大陸慣用語**簡體中文版本，保留全文與作者口吻。
3. 寫入三語系相同路徑與 metadata；需要時填入已存在的真實程式碼 repo 連結。
4. 執行 `python -m unittest discover -s tests -v` 與 `python scripts/build_site.py`，確認前後台的內容檢查、首頁推薦和三語系頁面成功。
5. 將三篇文章一起提交到 `company-notes/website` 的 `main`；GitHub Actions 自動部署 GitHub Pages。
6. 發佈後檢查 `/`、`/en/`、`/zh-hans/` 對應文章頁面，及相關首頁與分類索引。若 CI／部署失敗，必須如實回報，不要把「已提交」誤說為「已上線」。

## 5. 文章範例

2026-10-22 首篇親筆實戰文章：
- 繁體：`/blog/grok-bot-backup/`
- English：`/en/blog/grok-bot-backup/`
- 简体：`/zh-hans/blog/grok-bot-backup/`
- 配套原始碼：<https://github.com/company-notes/grok-bot-backup>

這篇保留作者「我叫 Grok Bot 自己寫備份」的第一人稱原意，僅修標點／大小寫／重複句、補上連結；未改寫成宣傳稿。

## 6. 工具箱裡的實用工具

- `toolkit/index.md` 也是由 `scripts/render_home.py` 自動生成，**不可直接手改**。
- 要在工具箱加上「可直接使用的外部 Bot、開源專案」等非文章資源，請修改 `templates/toolkit_resources.json`。每個資源可有名稱、簡介與多個連結（例如直接匯入 Bot、GitHub 原始碼）。
- 三種語系 `zh-hant`、`en`、`zh-hans` 都要新增同一資源，並分別在地化名稱、描述與按鈕文字；簡體中文用中國大陸慣用語，如「导入、备份、本地、源代码」。
- 工具箱原有的 Blog Toolkit 分類文章仍會自動列在這些可用工具下方。新增或調整分類文章仍依原有 frontmatter 流程，不得手動改生成頁面。
- 新增後以 `python -m unittest discover -s tests -v` 測試三語系是否都有 Bot 與 GitHub 連結，再由 GitHub Actions 建置部署。

2026-10-23 範例：Grok Bot 備份助理 `https://x.ai/bot/LvdHazZLidr0S3JJAdr8e`，對應原始碼 `https://github.com/company-notes/grok-bot-backup`。
