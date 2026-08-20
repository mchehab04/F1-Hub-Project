# Stage 08 — Multi-agent orchestration setup (Codex + Gemini)

**Date**: 2026-08-21
**Status**: Complete

## What was done

Checked the `multi-agent-mcp-orchestration` skill (user-requested) and set up the full split originally proposed: Codex implements backend, Gemini implements frontend, Claude orchestrates and reviews both.

## Key findings and decisions

- **Prerequisites were missing**: Node.js, Codex CLI, and Gemini CLI were not installed on this machine. Installed Node.js LTS (winget) and both CLIs (`npm install -g @openai/codex @google/gemini-cli`).
- **Gemini cannot be an MCP server** — checked `gemini mcp --help` directly rather than assuming; it only supports Gemini *consuming* other MCP servers, not exposing itself as one. Codex does support this (`codex mcp-server`, confirmed via `codex --help`). This means the two integrations are asymmetric: Codex is wired in as a true MCP server; Gemini is invoked headlessly via CLI (`gemini --skip-trust -p "..."`).
- **This session runs as a VS Code extension**, not the standalone `claude` CLI, so `claude mcp add` wasn't the right registration path. Used the `update-config` skill to confirm the actual mechanism: a project-level `.mcp.json` defining the server, plus `enabledMcpjsonServers` in `.claude/settings.json` to pre-approve it without a manual trust prompt.
- **Auth**: Codex was already logged in (ChatGPT). Gemini needed setup — the interactive OAuth login wasn't attempted given the earlier friction with `gh auth login`'s device-code flow getting stuck in this sandboxed shell environment; used a `GEMINI_API_KEY` (from Google AI Studio) set as a persistent Windows user environment variable instead, which is fully non-interactive. Verified with a headless test call (`gemini --skip-trust -p "..."` returned correctly).

## Files created/touched

- `.mcp.json` — registers `codex-backend` MCP server
- `.claude/settings.json` — pre-approves `codex-backend`
- `docs/orchestration.md` — full dispatch pattern, role split (Codex→backend, Gemini→frontend, Claude→orchestrate+review), cost awareness, and quality-control guidance (route non-trivial worker output through `subagent-verification` before merging)
- `.claude/CLAUDE.md` — added rule 2, pointing future work at `docs/orchestration.md`

## Verification

Confirmed `codex mcp-server` and `gemini mcp` subcommands exist via `--help` rather than trusting the skill's demo (which only covered Codex). Confirmed Codex auth (`codex login status`). Confirmed Gemini auth with a real headless call, not just an API-key-set check.

## Not yet done

- `codex-backend` hasn't been exercised yet as a live MCP tool in-session — new MCP servers only load at session start, so this needs a session restart/reload before Claude can actually dispatch to it. Flagged in `docs/orchestration.md`.
- No actual backend/frontend implementation has been dispatched to either worker yet — this stage was setup only.

## Next stage

Restart/reload the session to pick up `codex-backend`, then dispatch the first real implementation task (likely the ETL layer or the first FastAPI router) to test the orchestration end-to-end.
