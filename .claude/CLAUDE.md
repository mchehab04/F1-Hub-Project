# Agent Instructions

Read this entire file before starting any task.

## Self-Correcting Rules Engine

This file contains a growing ruleset that improves over time. **At session start, read the entire "Learned Rules" section before doing anything.**

### How it works

1. When the user corrects you or you make a mistake, **immediately append a new rule** to the "Learned Rules" section at the bottom of this file.
2. Rules are numbered sequentially and written as clear, imperative instructions.
3. Format: `N. [CATEGORY] Never/Always do X — because Y.`
4. Categories: `[STYLE]`, `[CODE]`, `[ARCH]`, `[TOOL]`, `[PROCESS]`, `[DATA]`, `[UX]`, `[OTHER]`
5. Before starting any task, scan all rules below for relevant constraints.
6. If two rules conflict, the higher-numbered (newer) rule wins.
7. Never delete rules. If a rule becomes obsolete, append a new rule that supersedes it.

### When to add a rule

- User explicitly corrects your output ("no, do it this way")
- User rejects a file, approach, or pattern
- You hit a bug caused by a wrong assumption about this codebase
- User states a preference ("always use X", "never do Y")

### Rule format example

```
14. [CODE] Always use `bun` instead of `npm` — user preference, bun is installed globally.
15. [STYLE] Never add emojis to commit messages — project convention.
16. [ARCH] API routes live in `src/server/routes/`, not `src/api/` — existing codebase pattern.
```

---

## Learned Rules

<!-- New rules are appended below this line. Do not edit above this section. -->

1. [PROCESS] Always write a short report after completing each stage/task and save it under `docs/reports/` — because the user wants a running, readable record of what was done and why at each step, not just the resulting code/artifacts. One file per stage, numbered in completion order (e.g. `01-feature-scoping.md`), covering: what was done, key decisions, outcomes, and files touched.
2. [ARCH] Backend implementation work goes through the Codex MCP server (`codex-backend` in `.mcp.json`); frontend implementation work goes through Gemini CLI headlessly (`gemini --skip-trust -p "..."`) — see `docs/orchestration.md` for the full dispatch pattern, role split, and why the two integrations aren't symmetric (Gemini has no MCP server mode). Read that file before dispatching backend/frontend implementation tasks.
3. [PROCESS] When a backend and a frontend chunk are independent (check `docs/api-contract.md` first), dispatch both in one message — Codex blocking + Gemini via `Bash({ run_in_background: true })` — and review/test whichever comes back first rather than waiting for both, per the "Parallel dispatch" section of `docs/orchestration.md` — because the Codex MCP tool has no async mode so this is the only way to get real concurrency, and polling for the backgrounded one wastes turns.
