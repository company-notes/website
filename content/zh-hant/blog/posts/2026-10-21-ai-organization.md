---
title: "先替 AI 團隊畫好組織圖"
date: 2026-10-21
slug: ai-organization
description: "Bot 可以做什麼、誰要核准，以及權限應該在哪一層控制。"
categories: [Playbooks]
tags: [AI-organization, permissions]
featured: true
featured_order: 2
featured_image: assets/covers/organization.svg
featured_image_alt: "以圖形節點和連線呈現的 AI 組織分工插畫"
status: review
---
# 先替 AI 團隊畫好組織圖

企業使用 AI Bots，不應只是建立大量角色。首先要回答：每個角色**有權做什麼**、**必須完成什麼**，以及**哪些情況需要人批准**。

<!-- more -->

![先替 AI 團隊畫好組織圖](../../assets/covers/organization.svg)

## 一份可實作的角色卡

| 欄位 | 範例 |
| --- | --- |
| 角色 | 客戶郵件助理 |
| 輸入 | 授權信箱的指定郵件 |
| 輸出 | 已分類需求、回信草稿 |
| 工具 | 有範圍限制的 Mail / Task MCP |
| 禁止 | 自行確認報價、修改銀行帳戶 |
| 驗收 | 人工審核後再對外送出 |

!!! note "設計原則"
    權限必須由系統層的授權檢查執行，而不是只寫在 Prompt 裡。

這是公開方法範本，不代表女媧內部所有 Bots 的實際配置。
