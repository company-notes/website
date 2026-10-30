---
title: "A Must-Have for Working with an AI Team: Build Your Own Free Typeless Alternative"
date: 2026-10-29
slug: openwhispr-groq-cloudflare-typeless
description: "How I combined OpenWhispr, Groq Whisper, Cloudflare Workers AI, and my own Worker to build a dictation setup that fits my daily use within the free tiers."
categories: [Field Notes]
tags: [OpenWhispr, Groq, Cloudflare, Workers-AI, speech-to-text, dictation]
featured: true
featured_order: 2
featured_image: assets/covers/integrations.svg
featured_image_alt: "Illustration of connected AI systems"
status: published
---

# A Must-Have for Working with an AI Team: Build Your Own Free Typeless Alternative

These days, a lot of the people we work with have effectively been replaced by AI. And the way we talk to AI is usually by typing. That's become a bottleneck. We used to talk to actual people much faster. At a company built mainly around an AI team, I spend almost every day talking to AI rather than to people. But typing furiously at AI in Codex or Claude CLI, or in Grok Bot, takes up a lot of time.

Typeless gave us an enormous boost in efficiency. Voice input like this used to struggle with recognition accuracy. Now, with LLMs cleaning up text behind the scenes and advances in speech models, dictation is much better than it used to be, and several times faster than typing. But here's the problem: Typeless is expensive. So I started looking for something simpler and cheaper.

<figure class="cn-post-video" style="box-sizing:border-box;width:calc(100% - 1rem);max-width:520px;margin:1.25rem auto 1.65rem;text-align:center">
  <video controls playsinline preload="metadata" width="520" height="444" style="display:block;width:100%;max-width:520px;height:auto;margin:0 auto;" poster="../../assets/posts/openwhispr-typeless/My_Typeless_poster.jpg" aria-label="Demonstration of the finished OpenWhispr dictation setup">
    <source src="../../assets/posts/openwhispr-typeless/My_Typeless.mp4" type="video/mp4">
    Your browser cannot play this video. Download the MP4 instead. <a href="../../assets/posts/openwhispr-typeless/My_Typeless.mp4">MP4</a>
  </video>
  <figcaption>The final result</figcaption>
</figure>

First I tried Handy. Its big selling point is that it can run entirely locally, with local models and no cloud involved. That's great for privacy. The problem is, my GPU is a fossil, and RAM is pretty tight too. After testing for a while, I found that the fast, lightweight models were basically garbage at recognition, especially when technical jargon and everyday conversation are mixed together, as they are for us. And the models that actually recognized speech well ate all my RAM. So I started exploring free cloud models instead.

After looking into OpenLess and OpenWhispr, I found OpenWhispr's user experience far better than OpenLess. That got me thinking: could I use OpenWhispr with Cloudflare Workers AI to clean up the sentences, and Groq's Whisper for speech recognition? Whisper on Groq is fast, and its free tier is enough for my use. For individual use, the free tiers of both have been enough for my daily work.

Here's how I put it together.

<!-- more -->

---

## The combination I use

The whole process is actually pretty simple. It has three parts:

1. **OpenWhispr**: A Windows voice-input tool. It handles recording, keyboard shortcuts, and inserting the final text into the program you're using.
2. **Groq Whisper**: Converts speech to text. I'm using `whisper-large-v3`; if speed matters more, you can also try `whisper-large-v3-turbo`.
3. **Cloudflare Workers AI + Qwen3**: Cleans up recognized text, removing filler words and fixing punctuation and obvious slips of the tongue. A Cloudflare Worker sits in the middle so OpenWhispr can call it through an OpenAI-compatible interface.

The flow looks like this:

```text
Press the OpenWhispr recording shortcut
                 ↓
             Groq Whisper
           Speech to text
                 ↓
      Cloudflare Worker (adapter)
                 ↓
    Cloudflare Qwen3-30B-A3B-FP8
  Clean up filler words, punctuation,
         and slips of the tongue
                 ↓
      OpenWhispr inserts the text
```

This setup doesn't need a big speech-recognition model running on my local GPU. But it's **not an offline setup**: audio goes to Groq, and the transcript goes to Cloudflare. If you enable the fallback described later, the text may also be sent to Groq's LLM.

## Step 1: Install OpenWhispr

Go to the [official OpenWhispr download page](https://openwhispr.com/download) and install the Windows version.

It's also open source: [OpenWhispr on GitHub](https://github.com/OpenWhispr/openwhispr).

Follow the setup wizard on first launch. Since we'll use our own API keys, there's no need to subscribe to OpenWhispr Cloud just to get basic voice input working.

Once it's installed, open Settings. We'll configure speech recognition first, then AI text cleanup, so that if something goes wrong, it's easier to tell which part is responsible.

## Step 2: Use Groq Whisper for speech recognition

First, create an API key in the [Groq Console](https://console.groq.com/keys).

Then open OpenWhispr:

**Settings → AI Models → Speech-to-text → Dictation → Cloud Provider**

Choose **Groq**, or use a custom OpenAI-compatible endpoint as shown in my screenshot:

| Setting | Value |
| --- | --- |
| Mode | Cloud Provider |
| Endpoint URL | `https://api.groq.com/openai/v1` |
| API Key | Your own Groq API key (typically starts with `gsk_`) |
| Model | `whisper-large-v3` |

If you want more speed, try `whisper-large-v3-turbo`. The screenshot shows my `whisper-large-v3` setting. Both can handle multilingual speech recognition.

![OpenWhispr speech-to-text settings with Groq Whisper; API key redacted](../../assets/posts/openwhispr-typeless/01-groq-whisper.webp)

For the first test, **leave AI text cleanup disabled**. Open Notepad or any text field, speak a few sentences, and make sure recording and automatic insertion work correctly.

Interestingly, Groq's Whisper already does some basic text cleanup. If I say something like, "Okay, let me try again, I mean, uh…", it may drop some of the "uh" and pauses. That's still different from the LLM cleanup we'll add next.

## Step 3: Prepare Cloudflare Workers AI

Now we need to make the recognized text sound more natural.

I'm using Qwen3 on Cloudflare Workers AI:

```text
@cf/qwen/qwen3-30b-a3b-fp8
```

Putting a Workers AI URL directly into OpenWhispr doesn't necessarily work perfectly, especially because Qwen3's thinking output and normal text output have different formats. I actually ran into a case where the API returned HTTP 200 but there was no usable final text.

So I put a **Cloudflare Worker** between them to forward requests and handle response-format compatibility.

### 3-1. Create a Cloudflare account and API token

Log in to the [Cloudflare Dashboard](https://dash.cloudflare.com/).

In Workers AI, obtain:

- **Cloudflare Account ID**
- **Workers AI API Token**

You can follow the [official Cloudflare REST API guide](https://developers.cloudflare.com/workers-ai/get-started/rest-api/) to create the token.

The Account ID identifies the account; the API token is a secret. **Never put it in a public GitHub repo, tutorial, or screenshot.**

### 3-2. Create the Worker

In the Cloudflare Dashboard, open **Workers & Pages** and create a Worker. The interface may change; if you see **Start with Hello World** or a blank Worker option, either is fine.

Then open **Edit Code** and replace the sample with `worker.js` from this GitHub project:

**GitHub project:** [Dictation Cleaner](https://github.com/company-notes/dictation-cleaner)  
**Worker source:** [`worker.js`](https://github.com/company-notes/dictation-cleaner/blob/main/worker.js)  
**Full deployment instructions:** [`README.md`](https://github.com/company-notes/dictation-cleaner/blob/main/README.md)

Paste in the code and click **Deploy**. Next, go to the Worker's **Settings → Variables and Secrets → Add** and set:

| Variable | Type | Value |
| --- | --- | --- |
| `CF_ACCOUNT_ID` | **Text** | Your Cloudflare Account ID (32 hexadecimal characters) |

Save and deploy the updated settings. **This is the only required Worker environment variable.** You don't need to save the Workers AI API token in the Worker itself. You'll enter it into OpenWhispr's API Key field later, and the Worker will pass it on to Cloudflare.

That way, neither someone's Account ID nor their token needs to be hard-coded in the public source.

Other model names, API URLs, input-size limits, and language hints can be overridden with optional Worker variables. **If you don't set them, the defaults apply.** For example:

| Optional variable | Default |
| --- | --- |
| `CHAT_MODEL` | `@cf/qwen/qwen3-30b-a3b-fp8` |
| `GROQ_CHAT_MODEL` | `qwen/qwen3.8-27b` |
| `ASR_MODEL` | `@cf/openai/whisper-large-v3-turbo` |
| `DEFAULT_ASR_LANGUAGE` | `zh` |
| `ASR_VOCAB_HINT` | Built-in technical vocabulary hints |

You can also customize `GROQ_CHAT_URL`, `ASR_ALIASES`, `MAX_CHAT_BYTES`, `MAX_AUDIO_BYTES`, and `MAX_MULTIPART_BYTES`. They're not required for this setup. See the [environment variable section of the GitHub README](https://github.com/company-notes/dictation-cleaner#deploy-in-cloudflare) for exact names, defaults, and formats.

After deployment, you'll get a URL similar to:

```text
https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev
```

You can check it in your browser at:

```text
https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev/health
```

The code version used for this article is **v2.8**. When configured correctly, `/health` should return JSON with `"ok": true` and `"version": "2.8.0"`. If you see a 503 mentioning `CF_ACCOUNT_ID`, the environment variable is probably missing or invalid.

**Note:** The URL you'll enter in OpenWhispr later must end in `/v1`, but the `/health` test URL does not.

## Step 4: Configure AI text cleanup in OpenWhispr

Back in OpenWhispr, go to:

**Settings → AI Models → Language Model → Dictation Cleanup**

Switch on **Enable Text Cleanup**.

For the provider, choose **Self Hosted**. Despite the name, we're not running the model on our own computer; we're pointing it at the Cloudflare Worker we deployed.

| Setting | Value |
| --- | --- |
| Text Cleanup | On |
| Provider | Self Hosted |
| Endpoint URL | `https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev/v1` |
| API Key | Your Cloudflare Workers AI token from earlier (forwarded by the Worker) |
| Model | `@cf/qwen/qwen3-30b-a3b-fp8` |
| Disable Thinking Output | On |

![OpenWhispr dictation cleanup and Cloudflare Worker endpoint settings; private URL and API key redacted](../../assets/posts/openwhispr-typeless/02-cloudflare-cleanup.webp)

Then click **Refresh** to fetch the available models. If everything is working, you'll see:

```text
@cf/qwen/qwen3-30b-a3b-fp8
```

Select it and enable **Disable Thinking Output**. This matters. I previously had the model return only thinking information with no normal `content`, which is why the Worker also handles the compatibility issue.

### 4-1. Adjust the prompt

Scroll farther down on the same screen to **Prompt Studio**, where you can view, customize, and test the prompt OpenWhispr uses for text cleanup.

I don't want it to rewrite what I've said. I want it to **preserve my meaning and only fix clear verbal mistakes, filler words, and punctuation**.

For example, you could add instructions like these (the example intentionally asks for Traditional Chinese as used in Taiwan):

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

It's just an example you can adjust; you don't need to copy it word for word. OpenWhispr already has a built-in cleanup prompt, so you can start with that and refine it over time.

![Qwen3 model selection, disabled thinking output, and Prompt Studio; sensitive information redacted](../../assets/posts/openwhispr-typeless/03-prompt-studio.webp)

## Step 5: Set a shortcut and start dictating

Go to OpenWhispr's **Shortcuts** settings and choose a shortcut you're comfortable with, one that won't conflict with other programs.

I'd start with a quick Notepad test:

1. Click inside the text area in Notepad.
2. Press the recording shortcut and speak normally.
3. Release the key or press it again to stop, depending on your recording mode.
4. Wait for Groq to recognize the speech and Qwen3 to clean it up, then see whether OpenWhispr inserts the final text automatically.

If you only want to check whether speech recognition works, temporarily turn off **Enable Text Cleanup**. OpenWhispr can still handle dictation on its own, which is one of the things I really like about it.

When I tried OpenLess, I ran into problems with it not working properly after I disabled the text model, and with the shortcut interfering with typing in Notepad. OpenWhispr has been much better in that respect on my Windows setup.

## Step 6 (optional): Automatically switch to Groq when Cloudflare runs out of quota

I later added a little feature to the Worker.

Normally, cleanup uses Qwen3 on Cloudflare first. But when Cloudflare specifically reports that the **daily free allowance has been exhausted**, the Worker can forward that same cleanup request to a Groq text model instead.

The fallback uses a different Qwen model offered by Groq, **not the identical model on Cloudflare**, so its output style may differ a little.

To enable it:

1. Open the Cloudflare Worker's **Settings → Variables and Secrets**.
2. Add a variable of type **Secret**.
3. Name it `GROQ_API_KEY`.
4. Enter your own Groq API key, save, and deploy.

This is optional. Without `GROQ_API_KEY`, the normal Cloudflare Qwen3 path still works; it just won't automatically fall back when Cloudflare's allowance is used up.

The Worker only switches for specific **quota-exhaustion errors**, not for every API error. Groq has its own allowances and limits, too, so this doesn't mean unlimited free use forever.

## A few things to keep in mind

- **Free doesn't mean unlimited.** Groq and Cloudflare can change their free allowances, available models, and billing rules. If your usage exceeds the free tier, check whether you've enabled paid billing.
- **This isn't a fully local privacy setup.** Audio goes to Groq and cleanup text goes to Cloudflare; if the fallback is enabled, text may also be sent to Groq's LLM. It's not suitable for sensitive content you don't want in the cloud.
- **Don't publish API keys.** The Workers AI token goes in OpenWhispr's API Key field and is forwarded by the Worker, not included in `worker.js` or GitHub. `CF_ACCOUNT_ID` is a regular Worker Text variable; only the optional `GROQ_API_KEY` should be added as a Worker Secret.
- **Mixed Chinese/English dictation and Traditional/Simplified conversion can still go wrong.** The ASR might mishear technical terms, and OpenWhispr's Chinese conversion might even change a correct character into the wrong one. Check the original transcript, cleaned text, and Chinese writing settings rather than blaming every issue on a single model.
- **Test one part at a time the first time.** Start with plain Groq transcription, then turn on Qwen3 cleanup, and only then add the fallback. That makes troubleshooting much easier.

---

My experience so far has been great. It's very usable, and it's fast. I actually dictated this entire article using the setup. Of course, I still had to proofread it and make a few small edits. But for someone like me who just wanted a free alternative, it's been more than good enough.

I hope it helps. Give it a try!