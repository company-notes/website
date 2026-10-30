---
title: "和 AI 團隊工作的神器：自己搭一套免費的 Typeless 替代方案"
date: 2026-10-29
slug: openwhispr-groq-cloudflare-typeless
description: "我用 OpenWhispr、Groq Whisper 和 Cloudflare Workers AI 的 Qwen3 搭配自建 Worker，做出免費額度足夠日常使用的語音輸入方案，分享完整設定與實測心得。"
categories: [Field Notes]
tags: [OpenWhispr, Groq, Cloudflare, Workers-AI, speech-to-text, dictation]
featured: true
featured_order: 2
featured_image: assets/covers/integrations.svg
featured_image_alt: "AI 系統串接的插畫封面"
status: published
---

# 和 AI 團隊工作的神器：自己搭一套免費的 Typeless 替代方案

這年頭，我們的協作對象，很大程度地從真人變成了 AI，而和 AI 對話的途徑，更常見的是使用打字，但這變成了一種瓶頸。過去我們和真人說話速度很快。在一個以 AI 團隊為主的公司裡面，我幾乎每天都在和 AI 說話，而不是在和真人說話。可是對著 AI 猛打，在 Codex 或 Claude 的 CLI、Grok Bot 裡面，打字佔去了很多的時間。

而 Typeless 的出現，給了我們很大的效率提升。過去這類的語音輸入法都有一些辨識能力不足的問題。現在透過 LLM 在背後校正，還有語音模型的進步，這樣的打字輸入已經比以前好很多了，速度足足是打字的好幾倍以上。但問題來了，Typeless 很貴。因此我就在研究有沒有簡單又便宜的方法。

<figure class="cn-post-video" style="box-sizing:border-box;width:calc(100% - 1rem);max-width:520px;margin:1.25rem auto 1.65rem;text-align:center">
  <video controls playsinline preload="metadata" width="520" height="444" style="display:block;width:100%;max-width:520px;height:auto;margin:0 auto;" poster="../../assets/posts/openwhispr-typeless/My_Typeless_poster.jpg" aria-label="OpenWhispr 語音輸入最後成果示範">
    <source src="../../assets/posts/openwhispr-typeless/My_Typeless.mp4" type="video/mp4">
    你的瀏覽器無法播放影片，可直接下載 MP4。 <a href="../../assets/posts/openwhispr-typeless/My_Typeless.mp4">MP4</a>
  </video>
  <figcaption>最後的成果</figcaption>
</figure>

一開始我試用了 Handy。Handy 的訴求是可以完全在本機進行，使用本機的模型，不必碰到雲端，這對隱私是非常好的。可問題就在於我的 GPU 是古董啊，RAM 也很吃緊。測試了一陣子，速度快又不吃資源的模型，辨識能力基本都是垃圾。尤其是像我們這種技術名詞和正常對話都會交錯的狀況。但好的辨識模型，直接把我的 RAM 都吃光了。因此我轉而開始研究雲端免費模型的可能。

在研究了 OpenLess、OpenWhispr 之後，OpenWhispr 的使用體驗完勝 OpenLess。所以我就想，我可以透過 OpenWhispr，使用 Cloudflare 的 Workers AI 對句子進行校正；至於語音模型的部分，使用 Groq 的 Whisper，速度又快，免費方案也足夠用。對於個人使用，這兩個的免費方案都足以支應日常的工作及使用。

下面就來說說，我是怎麼進行的。

<!-- more -->

---

## 我使用的組合

其實整個流程很單純，拆成三個部分：

1. **OpenWhispr**：Windows 上的語音輸入工具，負責錄音、快捷鍵，以及把最後的文字輸入到你正在使用的程式裡。
2. **Groq Whisper**：把聲音轉成文字。我目前使用 `whisper-large-v3`，如果更在意速度，也可以試試 `whisper-large-v3-turbo`。
3. **Cloudflare Workers AI + Qwen3**：把辨識完的文字再整理一次，移除贅字、修正標點和明顯口誤。中間透過一個 Cloudflare Worker，讓 OpenWhispr 可以用相容 OpenAI 的方式呼叫它。

流程大概是：

```text
按下 OpenWhispr 的錄音快捷鍵
             ↓
        Groq Whisper
         語音轉文字
             ↓
   Cloudflare Worker（轉接）
             ↓
 Cloudflare Qwen3-30B-A3B-FP8
    修正贅字、標點和口誤
             ↓
    OpenWhispr 輸入文字
```

這套方案不需要讓本機 GPU 跑大型語音辨識模型。但它**不是離線方案**：錄音會送到 Groq，轉錄文字會送到 Cloudflare；如果啟用後面提到的備援，文字也可能送到 Groq 的 LLM。

## 第一步：安裝 OpenWhispr

先到 [OpenWhispr 官方下載頁面](https://openwhispr.com/download)下載 Windows 版本並安裝。

它也有開源專案：[OpenWhispr GitHub](https://github.com/OpenWhispr/openwhispr)。

第一次啟動時，按照設定精靈走完即可。因為我們打算自己使用 API Key，所以不用為了基本語音輸入另外訂閱 OpenWhispr Cloud。你甚至連帳號都不用建。

安裝好後，進入設定。我們先設定語音辨識，再設定 AI 文字整理，這樣有問題的時候比較容易知道是哪一段出了錯。

## 第二步：用 Groq Whisper 做語音辨識

先到 [Groq Console](https://console.groq.com/keys)建立一組 API Key。

然後打開 OpenWhispr：

**設定 → AI 模型 → 語音轉文字 → 聽寫 → 雲端供應商**

選擇 **Groq**，或像我截圖一樣使用「自訂」的 OpenAI 相容端點，填入：

| 設定 | 填入內容 |
| --- | --- |
| 模式 | 雲端供應商 |
| 端點 URL | `https://api.groq.com/openai/v1` |
| API Key | 你自己的 Groq API Key（通常以 `gsk_` 開頭） |
| 模型 | `whisper-large-v3` |

如果希望速度更快，可以先試 `whisper-large-v3-turbo`。我自己的截圖是 `whisper-large-v3`，兩個都可以用來做多語言語音辨識。

![OpenWhispr Groq Whisper 語音轉文字設定，API Key 已遮蔽](../../assets/posts/openwhispr-typeless/01-groq-whisper.webp)

設定後，先**不開啟 AI 文字整理**，到記事本或任何文字輸入框試著說幾句話，確認錄音和自動貼上都正常。

有趣的是，Groq 的 Whisper 本身就有基本的文字整理能力。例如我說「好，那我再試一次，就是，呃……」，它可能已經會省略部分「呃」和停頓。不過，這和後面 LLM 所做的潤稿仍然是兩回事。

## 第三步：準備 Cloudflare Workers AI

接下來要處理的是把轉錄後的文字變得更自然。

我使用 Cloudflare Workers AI 上的 Qwen3：

```text
@cf/qwen/qwen3-30b-a3b-fp8
```

但直接把 Workers AI 的網址填進 OpenWhispr，不一定能完整相容，尤其是 Qwen3 的思考輸出與一般文字輸出的格式。我實際測試時，就碰過 API 明明回傳 HTTP 200，最後卻沒有正常文字的問題。

所以我在中間放了一個 **Cloudflare Worker** 來轉接請求，並處理回應格式與相關的相容性問題。

### 3-1. 建立 Cloudflare 帳號與 API Token

先登入 [Cloudflare Dashboard](https://dash.cloudflare.com/)。

在 Workers AI 頁面取得：

- **Cloudflare Account ID**
- **Workers AI API Token**

可以參考 [Cloudflare 官方 REST API 教學](https://developers.cloudflare.com/workers-ai/get-started/rest-api/)建立 Token。

Account ID 是帳號識別資料；API Token 則是金鑰，**不要貼在公開 GitHub、教學文章或截圖裡**。

### 3-2. 建立 Worker

在 Cloudflare Dashboard 進入 **Workers & Pages**，建立一個新的 Worker。介面可能隨時間改變；如果看到 **Start with Hello World** 或建立空白 Worker 的選項，選它即可。

建立後，進入 **Edit Code（編輯程式碼）**，把原本的範例程式換成以下 GitHub 專案裡的 `worker.js`。

**GitHub 專案：**[Dictation Cleaner](https://github.com/company-notes/dictation-cleaner)  
**Worker 原始碼：**[`worker.js`](https://github.com/company-notes/dictation-cleaner/blob/main/worker.js)  
**完整部署說明：**[`README.md`](https://github.com/company-notes/dictation-cleaner/blob/main/README.md)

將程式碼貼上後按 **Deploy**，然後進入這個 Worker 的 **Settings → Variables and Secrets → Add**，新增以下設定：

| 變數名稱 | 類型 | 值 |
| --- | --- | --- |
| `CF_ACCOUNT_ID` | **Text** | 你自己的 Cloudflare Account ID（32 位十六進位字元） |

儲存並部署更新後的設定。**這是唯一必填的 Worker 環境變數**；Cloudflare Workers AI 的 API Token 不需要另外存到 Worker 裡面，稍後直接填入 OpenWhispr 的 API Key 欄位即可，由 Worker 轉送給 Cloudflare。

這樣公開的程式碼裡就不需要寫死任何人的 Account ID，也不需要把 Token 放在 GitHub 上。

其他模型名稱、API URL、輸入大小限制和語言提示等參數也可以透過 Worker 的環境變數自行覆寫；**不設定就沿用程式預設值**。例如：

| 選用變數 | 預設值 |
| --- | --- |
| `CHAT_MODEL` | `@cf/qwen/qwen3-30b-a3b-fp8` |
| `GROQ_CHAT_MODEL` | `qwen/qwen3.8-27b` |
| `ASR_MODEL` | `@cf/openai/whisper-large-v3-turbo` |
| `DEFAULT_ASR_LANGUAGE` | `zh` |
| `ASR_VOCAB_HINT` | 內建技術詞提示清單 |

像是 `GROQ_CHAT_URL`、`ASR_ALIASES`、`MAX_CHAT_BYTES`、`MAX_AUDIO_BYTES`、`MAX_MULTIPART_BYTES` 也都能自訂。這些參數不是本文方案的必填項目，完整名稱、預設值與格式請直接參考 [GitHub README 的環境變數說明](https://github.com/company-notes/dictation-cleaner#deploy-in-cloudflare)。

成功後會取得一個類似這樣的網址：

```text
https://你的-worker.你的帳號.workers.dev
```

可以先在瀏覽器開啟：

```text
https://你的-worker.你的帳號.workers.dev/health
```

本文使用的程式版本為 **v2.8**。設定正確時，`/health` 應該回傳包含 `"ok": true` 和 `"version": "2.8.0"` 的 JSON。如果看到 `503` 並提示 `CF_ACCOUNT_ID`，通常表示環境變數尚未設定或格式有誤。

**注意：** 接下來在 OpenWhispr 裡使用的網址要加上 `/v1`，但測試 `/health` 時不需要。

## 第四步：設定 OpenWhispr 的 AI 文字整理

現在回到 OpenWhispr：

**設定 → AI 模型 → 語言模型 → 聽寫清理**

把 **「啟用文字整理」** 打開。

供應方式選 **「自架主機」**。雖然名稱叫自架主機，但我們這裡並不是在自己電腦上執行模型，而是讓它連到自己部署的 Cloudflare Worker。

| 設定 | 填入內容 |
| --- | --- |
| 文字整理 | 開啟 |
| 供應方式 | 自架主機 |
| 端點 URL | `https://你的-worker.你的帳號.workers.dev/v1` |
| API Key | 前面建立的 Cloudflare Workers AI Token（由 Worker 直接轉送） |
| 模型 | `@cf/qwen/qwen3-30b-a3b-fp8` |
| 停用思考輸出 | 開啟 |

![OpenWhispr 聽寫清理設定，私人端點與 API Key 已遮蔽](../../assets/posts/openwhispr-typeless/02-cloudflare-cleanup.webp)

填好之後，按 **「重新整理」** 取得可用模型清單。如果一切正常，就能看到：

```text
@cf/qwen/qwen3-30b-a3b-fp8
```

選取這個模型，並開啟 **「停用思考輸出」**。這裡很重要：我之前就是因為模型只輸出思考資訊、沒有正常的 `content`，才需要在 Worker 裡處理相容性。

### 4-1. 調整提示詞

同一個畫面往下，可以看到 **「提示詞工作室」**，能檢視、修改並測試 AI 文字整理使用的提示詞。

我希望它做的事情不是幫我重新寫一篇文章，而是**盡量保留原意，只修正明顯口誤、贅字和標點**。

例如可以在自訂提示詞裡加入這類要求：

```text
你是一個台灣繁體中文的語音輸入校正助手。

請保留說話者原本的意思、語氣和個人風格。
移除沒有意義的「嗯、呃、那個、就是」以及意外重複。
如果說話者講錯後立刻改口，以最後明確表達的意思為準。
修正標點、明顯錯字和語音辨識錯誤，不要自行增加內容。
保留 model、Qwen3、API、Cloudflare、Codex 等技術詞的大小寫。
最終使用台灣繁體中文，注意「干擾／幹部」等依語意不同的用字。
只輸出整理後的文字，不要解釋。
```

這只是一個可自行調整的例子，不需要完全照抄。OpenWhispr 原本就有內建的清理 Prompt，可以先使用預設，再慢慢調整。

![Qwen3 模型、停用思考輸出、提示詞工作室畫面，敏感資訊已遮蔽](../../assets/posts/openwhispr-typeless/03-prompt-studio.webp)

## 第五步：設定快捷鍵，開始用語音打字

再到 OpenWhispr 的 **「快捷鍵」** 設定，選一組自己習慣、不會和其他程式衝突的快捷鍵。

我建議先在記事本測試：

1. 點進記事本的文字輸入區域。
2. 按下錄音快捷鍵，直接講話。
3. 依你選擇的錄音模式，放開按鍵或再次按鍵來停止。
4. 等待 Groq 辨識、Qwen3 整理，最後看 OpenWhispr 是否自動輸入文字。

如果你只是想先確認語音辨識有沒有成功，可以把「啟用文字整理」暫時關閉。OpenWhispr 仍然可以單獨做語音輸入，這是我覺得它很好用的地方。

我之前試 OpenLess 時，碰過關掉文字模型就無法正常使用，以及快捷鍵干擾記事本輸入的狀況；OpenWhispr 在我的 Windows 環境裡，這方面的體驗好很多。

## 第六步（選用）：Cloudflare 額度用完，自動切換 Groq

我後來又在 Worker 裡加入一個小功能。

正常情況下，文字整理仍然優先使用 Cloudflare 的 Qwen3；當 Cloudflare 明確回傳**每日免費額度耗盡**的錯誤時，再把同一次文字整理請求轉交 Groq 的文字模型。

備援使用的是 Groq 提供的另一款 Qwen 模型，**不是 Cloudflare 同一個模型**，所以輸出風格有可能稍有差異。

如果想啟用這個備援：

1. 到 Cloudflare Worker 的 **Settings → Variables and Secrets**。
2. 新增一個類型為 **Secret** 的變數。
3. 變數名稱填入 `GROQ_API_KEY`。
4. 值填入自己的 Groq API Key，儲存並部署。

這是選用功能。沒有設定 `GROQ_API_KEY`，一般情況下使用 Cloudflare Qwen3 仍然沒有問題；只是 Cloudflare 額度耗盡後，不會自動備援。

備援只會在 Worker 辨識到特定的**額度耗盡錯誤**時啟用，不是每一個 API 錯誤都會切換。Groq 也有自己的額度與使用限制，不能理解成永久無限免費。

## 幾個使用上的注意事項

- **免費不等於無限制。** Groq 和 Cloudflare 的免費額度、模型清單及計費規則都可能調整；如果使用量超過免費額度，請先確認自己是否啟用了付費計費。
- **這不是完全本機的隱私方案。** 錄音會送到 Groq，整理文字會送到 Cloudflare，備援啟用時還可能轉送 Groq 的 LLM。不適合直接拿來處理不希望上雲端的敏感資訊。
- **不要公開 API Key。** Cloudflare Workers AI Token 填在 OpenWhispr 的 API Key 欄位，由 Worker 直接轉送，不需要放進 `worker.js` 或 GitHub。`CF_ACCOUNT_ID` 是一般 Worker Text 變數；選用的 `GROQ_API_KEY` 才需要設定成 Worker Secret。
- **中英混說和繁簡轉換仍可能出錯。** 例如 ASR 可能把技術詞聽錯；OpenWhispr 的繁簡轉換也可能把正確的「干擾」變成「幹擾」。遇到這種狀況，可以檢查原始轉錄、文字整理結果與中文書寫設定，不要一股腦地認為是同一個模型的問題。
- **第一次使用先分段測試。** 先測 Groq 純辨識，再開啟 Qwen3 文字整理，最後才加備援。這樣比較容易排錯。

---

我實測的結果是非常好用，而且速度也快。我的這一整篇文章就是使用這個方案直接打出來的，當然中間還是需要校對，然後改一些小地方。但是對於我來說，只是想要一個免費的替代方案，已經非常好用了。

希望這對你有幫助，歡迎使用！