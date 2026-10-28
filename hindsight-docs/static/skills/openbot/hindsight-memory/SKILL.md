---
name: "Hindsight Memory"
description: "Use the connected Hindsight MCP tools as long-term memory: recall relevant context before acting, and retain durable new facts as you learn them."
---

# Hindsight Memory

Use this whenever the **Hindsight** app is connected. Hindsight is your long-term memory: it persists across threads, survives context compaction, and is shared with the other agents on the same bank. Do not rely on the thread alone to remember.

## Workflow

1. **Recall first.** At the start of a task — and before answering anything about the user, the project, past decisions, or prior work — call `recall` with the question or task in your own words. Use what it returns; do not guess when memory can tell you.
2. **Retain durable facts.** When the user states a preference, decision, fact, goal, or a result worth keeping, call `retain` to store it. Use `sync_retain` instead when you need to read it back in the same turn.
3. **Reflect for synthesis.** For a question that needs reasoning across many memories ("what do you know about X", "how should you approach this"), call `reflect` rather than a single `recall`.
4. **Tag for scope** when it helps later filtering (e.g. a project or user tag), and pass a short `context` category on retain.

## What not to store

- Secrets, credentials, or API keys.
- Transient chatter, acknowledgements, or anything only relevant to the current turn.
- Facts already in memory — recall first to avoid duplicates; correct a wrong memory instead of adding a contradicting one.

## Notes

- Memory is scoped to the **bank** in the connection's MCP URL. Agents sharing a bank share memory; give an agent its own bank URL for isolation.
- Retained facts are extracted and may be reworded — recall by meaning, not exact wording.
