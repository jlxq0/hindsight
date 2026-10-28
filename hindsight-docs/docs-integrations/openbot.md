---
sidebar_position: 42
title: "OpenBot Shared Agent Memory with Hindsight | Integration"
description: "Give your OpenBot teammates persistent long-term memory that outlives a single thread and is shared across the whole team — connect Hindsight's MCP server to any OpenBot agent."
---

# OpenBot

Give your [OpenBot](https://openbot.run) teammates a memory that lasts, powered by [Hindsight](https://hindsight.vectorize.io). OpenBot runs a team of persistent AI agents on your own computer — Claude, Codex, Grok, Gemini, OpenCode and more. Connect Hindsight as an MCP server and every agent can **recall** what it learned in earlier threads, **retain** new facts as it works, and **reflect** over everything it knows about you and your projects.

## Why this matters

OpenBot agents are persistent, but their context is not: each thread compacts as it fills, and what one agent learns is invisible to the next. OpenBot's built-in memory helps, but it's small (a few kilobytes per agent) and private to one agent. Hindsight adds a durable layer that sits beside it:

- **Recall** is semantic — it finds the relevant fact even when the words don't match.
- **Retain** keeps facts, experiences and decisions across threads and restarts.
- **Reflect** reasons over everything an agent knows to answer a question.
- **One shared bank** means the whole team draws on the same memory, instead of 17 agents each keeping their own stale copy.

## What it does

Connecting the Hindsight MCP server gives every OpenBot agent the Hindsight tools (`recall`, `retain`, `sync_retain`, `reflect`, mental-model and document tools). Point each agent — or your whole team — at a Hindsight **bank**, and:

- **Memory outlives the thread** — facts retained in one session are recalled in the next, after compaction, and after a restart.
- **Shared or isolated, your choice** — give the team one bank for shared memory, or give each agent its own bank for strict isolation. The bank is chosen by the MCP URL.
- **Same data everywhere** — the memory an OpenBot agent writes is the same bank your other Hindsight integrations and automations read, so they see one consistent view.

## Installation

> ✨ **Recommended:** [Hindsight Cloud](https://ui.hindsight.vectorize.io/signup) — sign up free, create a bank, grab an API key, and skip self-hosting.

### Via the OpenBot marketplace (recommended)

Open **Apps** in OpenBot, find **Hindsight**, and click **Connect**. You'll be asked for two values:

| Field   | Value                                                               |
| ------- | ------------------------------------------------------------------- |
| MCP URL | `https://api.hindsight.vectorize.io/mcp/<bank>/` (replace `<bank>`) |
| API key | Your Hindsight Cloud API key (`hsk_…`)                              |

Enable the app for the agents that should share the memory.

### Add it manually as a custom MCP server

You can wire Hindsight up today without the marketplace listing. In OpenBot's **server settings**, add a URL MCP server:

- **URL**: `https://api.hindsight.vectorize.io/mcp/<bank>/`
- **Header**: `Authorization: Bearer hsk_…`

## Self-hosting

Prefer to run Hindsight on your own machine? Start a local server and point the MCP URL at it:

```bash
pip install hindsight-all
export HINDSIGHT_API_LLM_API_KEY=your-openai-key
hindsight-api
```

Then use `http://localhost:8888/mcp/<bank>/` as the MCP URL. A local server with no auth needs no API key — leave that field blank.

## Choosing a bank

The bank is part of the MCP URL (`/mcp/<bank>/`), so each connection is scoped to exactly one bank — agents never have to pass a `bank_id`.

- **Team memory** — give every agent the same URL (e.g. `/mcp/team/`).
- **Per-agent memory** — give each agent its own URL (e.g. `/mcp/research-bot/`, `/mcp/ops-bot/`).

See the [MCP server reference](/developer/mcp-server) for the full tool list and bank-selection rules.

## Make it automatic (optional)

Connecting the app gives agents the memory _tools_ — but an agent only uses them when it decides to. To make memory habitual (recall before acting, retain durable facts as it learns), add the **Hindsight Memory skill**: [download `SKILL.md`](https://hindsight.vectorize.io/skills/openbot/hindsight-memory/SKILL.md), then in OpenBot save it to your local skill library and enable it for the agents that use Hindsight. It's a short instruction set that tells the agent when to call `recall`, `retain`, and `reflect`.

## Try it

Ask an agent to remember something, then start a fresh thread and ask it back:

> **Remember that we decided to standardize on Postgres for all new services.**

> _(new thread)_ **What database did we standardize on, and why?**

The second thread recalls the decision from Hindsight — even though its own context was empty.
