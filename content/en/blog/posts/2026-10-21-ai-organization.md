---
title: "Design the org chart before hiring a Bot"
date: 2026-10-21
slug: ai-organization
description: "What agents can do, what needs approval, and where permissions belong."
categories: [Playbooks]
tags: [AI-organization, permissions]
featured: true
featured_order: 2
featured_image: assets/covers/organization.svg
featured_image_alt: "Graphic nodes and connecting lines representing an AI organization"
status: review
---
# Design the org chart before hiring a Bot

A company doesn't become AI-operated by creating dozens of Bots. Start with what each role **may do**, **must deliver**, and **must send to a human for approval**.

<!-- more -->

![Design the org chart before hiring a Bot](../../assets/covers/organization.svg)

## A practical role card

| Field | Example |
| --- | --- |
| Role | Customer-email assistant |
| Input | Authorized messages in a dedicated mailbox |
| Output | Classified requests and reply drafts |
| Tools | Scoped Mail / Task MCP |
| Never do | Approve quotes or change payment details |
| Acceptance | Human reviews before external delivery |

!!! note "Principle"
    Enforce permissions in the underlying systems; prompt instructions are not access controls.

This is a public example, not a claim about every Bot in Nuwa's actual setup.
