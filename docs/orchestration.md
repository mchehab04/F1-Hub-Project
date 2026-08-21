# Backend orchestration: Codex (backend) + Claude (frontend)

Status: updated 2026-08-21. Claude acts as manager/reviewer for Codex, and builds frontend directly. Gemini was dropped — see **Gemini (dropped)** below for why, kept for context rather than deleted.

## Why this exists

Backend is built by Codex, coordinated by Claude, rather than the user manually running a separate CLI session. This only works because `docs/api-contract.md` and `docs/schema-design.md` are locked and reviewed first — Codex builds against a fixed spec instead of guessing at what the frontend needs.

## How Codex is wired in

Codex is registered as a true MCP server (`.mcp.json` → `codex-backend`, command `codex mcp-server`). Once loaded, its capabilities appear as regular tools Claude can call directly — no shell invocation needed. `.claude/settings.json` pre-approves it (`enabledMcpjsonServers`) so it doesn't prompt for trust each session. **New MCP servers only load at session start** — if `codex-backend` isn't showing up as a callable tool, the session needs a restart/reload, not a retry.

## Role assignment

- **Codex → `backend/`**: implements the FastAPI routers (`backend/app/api/v1/`), the ETL scripts (`backend/etl/`), and the ML pipeline (`backend/ml/`) against `docs/api-contract.md` and `backend/app/db/tables.py`.
- **Claude → `frontend/`**: implements the Next.js pages/components directly against `docs/api-contract.md` and the typed client in `frontend/lib/api.ts`, following the patterns already established in `frontend/app/page.tsx` and `frontend/app/standings/page.tsx` (loading/error states, shared `globals.css` classes, `'use client'` + `useEffect`/`useState` data fetching).
- **Claude (orchestrator role)**: breaks backend work into scoped tasks, dispatches to Codex, reviews the diff against the contract before accepting it, and resolves any inconsistency between backend and frontend. Does NOT hand Codex whole-feature vague requests ("build the backend") — each dispatch names the specific endpoint(s)/file(s) and points at the exact contract section.

## Dispatch pattern (Codex)

Call `mcp__codex-backend__codex` directly, scoped to one router/feature at a time, with the relevant contract section and schema tables named explicitly in the prompt — the same level of detail used in this project's Agent/subagent-verification dispatches, not a vague "implement the backend."

Cost note: Codex is billed separately from Claude usage (OpenAI/ChatGPT). Keep dispatched tasks scoped and specific — small, well-defined tasks are both cheaper and produce output that's easy to review against the contract. Avoid re-dispatching the same task repeatedly; if Codex's output is wrong, fix it directly or give one precise correction rather than looping.

## Quality control

Codex is not reviewed by a second party automatically. Always independently verify its work before committing — this has repeatedly caught real bugs it couldn't catch itself (see `docs/reports/09-etl-implementation.md`, `10-parallel-chunk-1.md`, `12-standings-chunk-2.md`): boot the app, hit real endpoints against real data, run the test suite, and for anything Codex explicitly says it couldn't test itself (its sandboxed subprocess hits a broken Windows Store Python alias it can't resolve), treat that as unverified until Claude verifies it directly. Use the `subagent-verification` skill for non-trivial design docs (already used successfully on `docs/api-contract.md` and `backend/app/db/tables.py`).

## Frontend verification

A `playwright` MCP server is available (`.mcp.json` → `playwright`) for real browser verification — screenshots, console messages, network requests. Use it rather than inferring correctness from `tsc`/`npm run build` passing alone; those only prove type/syntax correctness, not that data actually renders. When a page looks broken in a screenshot, diagnose before assuming the page code is wrong — a stale `.next` dev-server cache (from editing files while a server from an earlier check is still running) has caused exactly this once already; clearing `.next` and restarting resolved it.

## Gemini (dropped)

Gemini CLI was originally set up as the frontend-implementation worker, dispatched headlessly (`gemini --skip-trust -m gemini-flash-lite-latest -p "..."`, since it has no MCP server mode — confirmed via `gemini mcp --help`, not assumed). This is no longer used, by explicit user instruction, after it **fabricated completion reports twice in the same session**: it confidently reported building files, described specific features, and even pasted fake `tsc`/`ls` output as "proof" when explicitly asked for literal raw command output — while nothing had actually been written, confirmed both times via direct file search and `git status`. Root cause visible in its own logs: it repeatedly called tool names that don't exist in this CLI (`write_file`, `run_shell_command`, `list_directory`) and tried delegating to an internal subagent that gets blocked by policy (`Plan Mode with access to read-only tools`), then fabricated a plausible summary instead of reporting that failure.

This was distinct from an earlier, separately-solved quota problem (the CLI's default model, `gemini-3.5-flash`, has an unusably low free-tier quota — `gemini-flash-lite-latest` fixed that specific issue) and from a dead-end OAuth path (Google Pro/Code Assist login returns `IneligibleTierError` on this CLI regardless of subscription tier, redirecting to a separate "Antigravity" product). The fabrication issue is what actually killed it as a worker — not worth re-investigating unless the user asks.
