---
title: "OpenWhispr：免费替代 Typeless"
date: 2026-10-29
slug: openwhispr-groq-cloudflare-typeless
description: "我用 OpenWhispr、Groq Whisper 和 Cloudflare Workers AI 的 Qwen3，加上自己部署的 Worker，做了一套免费额度足够日常使用的语音输入方案，分享完整配置和实测体验。"
categories: [Field Notes]
tags: [OpenWhispr, Groq, Cloudflare, Workers-AI, speech-to-text, dictation]
featured: true
featured_order: 2
featured_image: assets/covers/integrations.svg
featured_image_alt: "AI 系统连接的插画封面"
status: published
---

# OpenWhispr：免费替代 Typeless

这些年，我们的协作对象很大程度上已经从真人变成了 AI。而我们跟 AI 对话，更多时候还是靠打字，这就变成了一个瓶颈。以前我们和真人说话速度很快。在一家主要靠 AI 团队运转的公司里，我几乎每天都在跟 AI 说话，而不是跟真人说话。但在 Codex 或 Claude 的 CLI、Grok Bot 里对着 AI 一顿猛敲，打字真的占掉了不少时间。

Typeless 的出现，确实让我们的效率提升了不少。以前这类语音输入法总有识别不准的问题。现在有 LLM 在背后做校正，加上语音模型本身也进步了，这种输入方式已经比以前好用很多，速度更是打字的好几倍。但问题来了：Typeless 很贵。所以我就开始琢磨，有没有简单又便宜的办法。

一开始我试了 Handy。它的卖点是完全在本地运行，使用本地模型，不用碰云端，这对隐私非常好。可问题是我的 GPU 已经是老古董了啊，内存也很吃紧。折腾了一阵子，速度快又不怎么占资源的模型，识别能力基本都是垃圾。尤其是像我们这种技术术语和日常聊天经常混在一起的情况。但识别效果好的模型，直接把我的内存吃光了。所以我转头开始研究云端免费模型的可能性。

研究过 OpenLess 和 OpenWhispr 之后，我觉得 OpenWhispr 的使用体验完全胜过 OpenLess。于是我就想：能不能用 OpenWhispr，再让 Cloudflare 的 Workers AI 整理句子？至于语音模型，交给 Groq 的 Whisper，速度快，免费套餐对我也够用了。就个人使用而言，这两边的免费额度足够支撑我日常的工作和使用。

下面就说说我是怎么弄的。

<!-- more -->

---

## 我用的组合

整个流程其实很简单，拆成三个部分：

1. **OpenWhispr**：Windows 上的语音输入工具，负责录音、快捷键，以及把最终文字输入到你正在使用的软件里。
2. **Groq Whisper**：把声音转成文字。我目前用的是 `whisper-large-v3`；如果更在意速度，也可以试试 `whisper-large-v3-turbo`。
3. **Cloudflare Workers AI + Qwen3**：再整理一次识别出来的文字，去掉赘词、修正标点和明显口误。中间用一个 Cloudflare Worker 转接，让 OpenWhispr 可以通过兼容 OpenAI 的接口来调用。

大致流程是：

```text
按下 OpenWhispr 的录音快捷键
             ↓
        Groq Whisper
         语音转文字
             ↓
   Cloudflare Worker（转接）
             ↓
 Cloudflare Qwen3-30B-A3B-FP8
     修正赘词、标点和口误
             ↓
    OpenWhispr 输入文字
```

这套方案不需要让本地 GPU 跑大型语音识别模型。但它**不是离线方案**：录音会发送到 Groq，转录文字会发送到 Cloudflare；如果启用了后面说的备用方案，文字也可能发给 Groq 的 LLM。

## 第一步：安装 OpenWhispr

先去 [OpenWhispr 官方下载页面](https://openwhispr.com/download)下载并安装 Windows 版本。

它也是开源项目：[OpenWhispr GitHub](https://github.com/OpenWhispr/openwhispr)。

第一次启动，跟着设置向导走完就行。因为我们打算用自己的 API Key，所以不需要为了基础语音输入额外订阅 OpenWhispr Cloud。

安装完成后进入设置。我们先配置语音识别，再配置 AI 文字整理。这样出了问题也更容易判断是哪一环没弄好。

## 第二步：用 Groq Whisper 做语音识别

先到 [Groq Console](https://console.groq.com/keys)创建一个 API Key。

然后打开 OpenWhispr：

**设置 → AI 模型 → 语音转文字 → 听写 → 云端提供商**

选择 **Groq**，或者像我的截图那样使用“自定义”OpenAI 兼容端点，填入：

| 设置 | 填写内容 |
| --- | --- |
| 模式 | 云端提供商 |
| 端点 URL | `https://api.groq.com/openai/v1` |
| API Key | 你自己的 Groq API Key（通常以 `gsk_` 开头） |
| 模型 | `whisper-large-v3` |

如果想要更快，可以先试试 `whisper-large-v3-turbo`。我自己的截图用的是 `whisper-large-v3`，两个都可以进行多语言语音识别。

![OpenWhispr Groq Whisper 语音转文字设置，API Key 已遮挡](../../assets/posts/openwhispr-typeless/01-groq-whisper.webp)

配置好后，先**不要开启 AI 文字整理**。打开记事本或任何文本框，说几句话，确认录音和自动输入都正常。

有意思的是，Groq 的 Whisper 本身就会做一些基本的文字整理。例如我说“好，那我再试一次，就是，呃……”，它可能已经会省掉部分“呃”和停顿。不过，这和后面 LLM 做的润色还是两回事。

## 第三步：准备 Cloudflare Workers AI

接下来要让转录后的文字更自然。

我使用 Cloudflare Workers AI 上的 Qwen3：

```text
@cf/qwen/qwen3-30b-a3b-fp8
```

但直接把 Workers AI 的地址填到 OpenWhispr 里，不一定能完全兼容，尤其是 Qwen3 的思考输出和普通文本输出格式不一样。我实际测试时就遇到过 API 明明返回 HTTP 200，却没有正常文字的情况。

所以我在中间加了一个 **Cloudflare Worker**，专门转发请求，处理响应格式和相关兼容性问题。

### 3-1. 创建 Cloudflare 账号和 API Token

先登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)。

在 Workers AI 页面获取：

- **Cloudflare Account ID**
- **Workers AI API Token**

可以参考 [Cloudflare 官方 REST API 教程](https://developers.cloudflare.com/workers-ai/get-started/rest-api/)创建 Token。

Account ID 是账号标识；API Token 是密钥，**不要放进公开的 GitHub 仓库、教程文章或截图里**。

### 3-2. 创建 Worker

在 Cloudflare Dashboard 进入 **Workers & Pages**，创建新的 Worker。界面可能随时间变化；如果看到 **Start with Hello World** 或创建空白 Worker 的选项，选它就行。

创建后进入 **Edit Code（编辑代码）**，把示例代码替换成下面 GitHub 项目里的 `worker.js`。

**GitHub 项目：**[Dictation Cleaner](https://github.com/company-notes/dictation-cleaner)  
**Worker 源代码：**[`worker.js`](https://github.com/company-notes/dictation-cleaner/blob/main/worker.js)  
**完整部署说明：**[`README.md`](https://github.com/company-notes/dictation-cleaner/blob/main/README.md)

粘贴代码后点击 **Deploy**，接着进入这个 Worker 的 **Settings → Variables and Secrets → Add**，添加：

| 变量名 | 类型 | 值 |
| --- | --- | --- |
| `CF_ACCOUNT_ID` | **Text** | 你自己的 Cloudflare Account ID（32 位十六进制字符） |

保存并部署更新后的配置。**这是唯一必填的 Worker 环境变量。** Cloudflare Workers AI 的 API Token 不需要另外保存在 Worker 里，后面直接填到 OpenWhispr 的 API Key 一栏，由 Worker 转发给 Cloudflare。

这样公开的代码里就不需要写死任何人的 Account ID，也不需要把 Token 上传到 GitHub。

模型名、API URL、输入大小限制、语言提示等参数，也可以通过 Worker 环境变量自行覆盖。**不设置就使用默认值**。例如：

| 可选变量 | 默认值 |
| --- | --- |
| `CHAT_MODEL` | `@cf/qwen/qwen3-30b-a3b-fp8` |
| `GROQ_CHAT_MODEL` | `qwen/qwen3.8-27b` |
| `ASR_MODEL` | `@cf/openai/whisper-large-v3-turbo` |
| `DEFAULT_ASR_LANGUAGE` | `zh` |
| `ASR_VOCAB_HINT` | 内置技术术语提示列表 |

像 `GROQ_CHAT_URL`、`ASR_ALIASES`、`MAX_CHAT_BYTES`、`MAX_AUDIO_BYTES`、`MAX_MULTIPART_BYTES` 也都可以自定义。这些不是本文方案的必填项，完整名称、默认值和格式请参考 [GitHub README 的环境变量说明](https://github.com/company-notes/dictation-cleaner#deploy-in-cloudflare)。

部署成功后会得到一个类似这样的地址：

```text
https://你的-worker.你的账号.workers.dev
```

可以先在浏览器打开：

```text
https://你的-worker.你的账号.workers.dev/health
```

本文使用的代码版本为 **v2.8**。配置正确时，`/health` 应返回包含 `"ok": true` 和 `"version": "2.8.0"` 的 JSON。如果看到 `503` 并提示 `CF_ACCOUNT_ID`，通常意味着环境变量没设置或格式不对。

**注意：** 之后在 OpenWhispr 中填写的 URL 要加上 `/v1`，但测试 `/health` 时不需要。

## 第四步：设置 OpenWhispr 的 AI 文字整理

现在回到 OpenWhispr：

**设置 → AI 模型 → 语言模型 → 听写清理**

打开 **“启用文字整理”**。

提供方式选择 **“自架主机”**。虽然名字叫自架主机，但我们并不是在自己的电脑上运行模型，而是让它连接自己部署的 Cloudflare Worker。

| 设置 | 填写内容 |
| --- | --- |
| 文字整理 | 开启 |
| 提供方式 | 自架主机 |
| 端点 URL | `https://你的-worker.你的账号.workers.dev/v1` |
| API Key | 之前创建的 Cloudflare Workers AI Token（由 Worker 直接转发） |
| 模型 | `@cf/qwen/qwen3-30b-a3b-fp8` |
| 停用思考输出 | 开启 |

![OpenWhispr 听写清理设置，私人端点和 API Key 已遮挡](../../assets/posts/openwhispr-typeless/02-cloudflare-cleanup.webp)

填好后点击 **“刷新”** 获取可用模型列表。如果一切正常，就能看到：

```text
@cf/qwen/qwen3-30b-a3b-fp8
```

选择这个模型，并打开 **“停用思考输出”**。这一步很重要：我之前就是因为模型只输出思考信息，没有正常的 `content`，才需要在 Worker 里处理兼容性。

### 4-1. 调整提示词

同一页面继续往下，就能看到 **“提示词工作室”**，可以查看、修改和测试 AI 文字整理使用的提示词。

我希望它做的不是帮我重写文章，而是**尽量保留原意，只修正明显口误、赘词和标点**。

例如可以在自定义提示词里加入这样的要求。这里保留了我实际使用的**台湾繁体中文**输出目标，想用其他书写习惯可以自行调整：

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

这只是一个可以自己调整的例子，不需要完全照抄。OpenWhispr 本身就有内置的整理 Prompt，可以先用默认设置，再慢慢修改。

![Qwen3 模型、停用思考输出和提示词工作室页面，敏感信息已遮挡](../../assets/posts/openwhispr-typeless/03-prompt-studio.webp)

## 第五步：设置快捷键，开始语音打字

再到 OpenWhispr 的 **“快捷键”** 设置，选一个自己顺手、又不会和其他软件冲突的快捷键。

建议先在记事本里试试：

1. 点击记事本的文本区域。
2. 按下录音快捷键，直接说话。
3. 根据选择的录音模式，松开按键或再次按键停止。
4. 等待 Groq 识别、Qwen3 整理，最后看看 OpenWhispr 是否自动输入文字。

如果只是想确认语音识别有没有成功，可以暂时关闭“启用文字整理”。OpenWhispr 还是可以单独完成语音输入，这也是我觉得它很好用的地方。

之前试 OpenLess 的时候，我碰到过关闭文字模型后就没法正常使用，以及快捷键干扰记事本输入的问题；在我的 Windows 环境里，OpenWhispr 这方面的体验好得多。

## 第六步（可选）：Cloudflare 额度用完，自动切换 Groq

后来我又在 Worker 里加了一个小功能。

正常情况下，文字整理仍优先使用 Cloudflare 的 Qwen3；但当 Cloudflare 明确返回**每日免费额度耗尽**的错误时，就把同一次文字整理请求转交给 Groq 的文字模型。

备用方案使用的是 Groq 提供的另一款 Qwen 模型，**不是 Cloudflare 上完全相同的模型**，所以输出风格可能会有些差别。

如果想开启这个备用功能：

1. 进入 Cloudflare Worker 的 **Settings → Variables and Secrets**。
2. 添加一个类型为 **Secret** 的变量。
3. 变量名填 `GROQ_API_KEY`。
4. 值填入自己的 Groq API Key，保存并部署。

这是可选功能。不设置 `GROQ_API_KEY`，平时用 Cloudflare Qwen3 还是没问题；只是 Cloudflare 额度耗尽后不会自动切换。

Worker 只会在识别到特定的**额度耗尽错误**时切换，而不是所有 API 错误都切换。Groq 自己也有额度和使用限制，不能当成永久免费无限量。

## 一些使用上的注意事项

- **免费不等于没有限制。** Groq 和 Cloudflare 的免费额度、模型列表、计费规则都可能调整。如果用量超过免费额度，请先确认是否开启了付费计费。
- **这不是完全本地的隐私方案。** 录音会发给 Groq，整理文字会发给 Cloudflare，开启备用功能后文字还可能发给 Groq 的 LLM。不适合拿来直接处理不希望上传云端的敏感信息。
- **不要公开 API Key。** Cloudflare Workers AI Token 填在 OpenWhispr 的 API Key 一栏，由 Worker 直接转发，不要写进 `worker.js` 或 GitHub。`CF_ACCOUNT_ID` 是普通 Worker Text 变量；可选的 `GROQ_API_KEY` 才需要设置成 Worker Secret。
- **中英混说和繁简转换还是可能出错。** 比如 ASR 可能听错技术术语；OpenWhispr 的繁简转换也可能把本来正确的“干擾”变成“幹擾”。遇到这类情况，可以分别检查原始转录、整理后的文本和中文书写设置，别把所有问题都算到同一个模型头上。
- **第一次使用最好分段测试。** 先测试 Groq 的纯识别，再开启 Qwen3 文字整理，最后添加备用功能。这样更容易排查问题。

---

我实测下来真的很好用，而且速度也快。这整篇文章就是我直接用这套方案说出来的。当然，中间还是要校对，再改一些小地方。但对我来说，我只是想找一个免费的替代方案，现在这样已经非常够用了。

希望能帮到你，欢迎试试！