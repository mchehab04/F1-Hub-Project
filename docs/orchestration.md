# Multi-agent orchestration: Codex (backend) + Gemini (frontend)

Status: set up 2026-08-21. Claude acts as manager/reviewer; Codex and Gemini implement.

## Why this exists

Backend and frontend are built by different AI tools running in parallel, coordinated by Claude rather than by the user manually running two separate CLI sessions. This only works because `docs/api-contract.md` and `docs/schema-design.md` are locked and reviewed first — both workers build against a fixed spec instead of guessing at each other's in-progress work.

## How each worker is wired in (they're NOT symmetric — read this before assuming both work the same way)

- **Codex** is registered as a true MCP server (`.mcp.json` → `codex-backend`, command `codex mcp-server`). Once loaded, its capabilities appear as regular tools Claude can call directly — no shell invocation needed. `.claude/settings.json` pre-approves it (`enabledMcpjsonServers`) so it doesn't prompt for trust each session. **New MCP servers only load at session start** — if `codex-backend` isn't showing up as a callable tool, the session needs a restart/reload, not a retry.
- **Gemini has no MCP server mode** (`gemini mcp` only lets Gemini *consume* other MCP servers, not act as one — confirmed by checking `gemini mcp --help`, not assumed). Gemini is instead invoked headlessly via Bash/PowerShell: `gemini --skip-trust -p "<prompt>"`. `--skip-trust` is required for non-interactive use in this workspace (see `GEMINI_CLI_TRUST_WORKSPACE`/trusted-folders docs). Auth is via `GEMINI_API_KEY` (persistent user env var), not OAuth — the interactive Google login flow wasn't usable from this environment's sandboxed shells (same class of issue hit earlier with `gh auth login`'s device-code flow).

## Role assignment

- **Codex → `backend/`**: implements the FastAPI routers (currently 501 stubs in `backend/app/api/v1/`), the ETL scripts (`backend/etl/`), and the ML pipeline (`backend/ml/`) against `docs/api-contract.md` and `backend/app/db/tables.py`.
- **Gemini → `frontend/`**: implements the Next.js pages/components against `docs/api-contract.md` and the typed client already in `frontend/lib/api.ts`.
- **Claude**: breaks work into scoped tasks, dispatches to the right worker, reviews the diff against the contract before accepting it, and resolves any inconsistency between the two sides. Claude does NOT hand off whole-feature vague requests ("build the backend") — each dispatch should name the specific endpoint(s)/file(s) and point at the exact contract section, matching how tasks were scoped throughout this project so far.

## Dispatch pattern

**To Codex** (once the MCP tools are live in-session): call its tool(s) directly, scoped to one router/feature at a time, with the relevant contract section and schema tables named explicitly in the prompt — the same level of detail used in this project's Agent/subagent-verification dispatches, not a vague "implement the backend."

**To Gemini** (headless CLI, via Bash/PowerShell):
```
gemini --skip-trust -p "<scoped task, with the exact contract endpoint(s)/component(s) and relevant files named>"
```
Capture and review the output/diff before treating it as done — Gemini is not reviewed by anyone else by default.

## Parallel dispatch

When a backend chunk and a frontend chunk are both ready and don't depend on each other's output (true for most contract-defined endpoint/component pairs), dispatch both in the **same message** rather than sequentially:

- The Codex MCP tool (`mcp__codex-backend__codex`) has no background/async mode — it's a blocking call. There's no way to make it non-blocking.
- The Gemini Bash call *can* run backgrounded: `Bash({ command: "gemini --skip-trust -p \"...\"", run_in_background: true })`.

So: issue the Codex call and the backgrounded Gemini call together. Codex's result returns as part of that same turn (it's the blocking one); review and test it immediately per Quality control below — don't wait on Gemini to start that review. Gemini's result arrives later as a background-task notification; when it lands, review/test that piece then. Don't poll for it.

This only saves wall-clock time when the two dispatched tasks are genuinely independent (e.g. no frontend component consumes a field the backend chunk hasn't shipped yet) — check that against `docs/api-contract.md` before dispatching in parallel.

## Cost awareness

Both are billed separately from Claude usage (OpenAI/ChatGPT for Codex, Google AI Studio for Gemini). Keep dispatched tasks scoped and specific — small, well-defined tasks are both cheaper and produce output that's actually easy to review against the contract. Avoid re-dispatching the same task repeatedly; if a worker's output is wrong, fix it directly or give one precise correction rather than looping.

## Quality control

Given neither worker is reviewed by a second party automatically, use the `subagent-verification` skill (or a direct review pass) on non-trivial output from either worker before merging — the same pattern already used successfully on `docs/api-contract.md` (caught 2 critical + 7 major issues) and `backend/app/db/tables.py` (smoke-tested before committing). Don't skip this just because a different tool wrote the code.
