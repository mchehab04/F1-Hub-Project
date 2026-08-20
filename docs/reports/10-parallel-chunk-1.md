# Stage 10 — Parallel chunk 1: season-overview backend + frontend

**Date**: 2026-08-21
**Status**: Backend chunk complete and verified. Frontend chunk blocked — not started.

## What was done

First test of the "small chunks, parallel tracks, verify before moving on" workflow: dispatched a scoped backend chunk to Codex and a scoped frontend chunk to Gemini simultaneously.

## Backend chunk 1 — ✅ complete, verified against real data

Codex implemented Pydantic schemas (`backend/app/schemas/{circuits,seasons,races}.py`) and real endpoint logic for `GET /circuits/{id}`, `GET /seasons`, `GET /seasons/{season}/races`, `GET /races/{race_id}`, replacing the 501 stubs. As with the ETL dispatch, Codex could not verify its own work (same broken-Python-sandbox issue as before, plus it couldn't see `f1hub.db` at all since it's gitignored/untracked).

Regenerated the database (FastF1's local cache made this fast — no re-download needed) and ran all four endpoints live:

- `GET /circuits/bahrain` → correct circuit data, lap record correctly attributed to Verstappen/2024
- `GET /seasons` → `{"seasons":[2024]}`
- `GET /seasons/2024/races` → correct 24-race calendar with circuit names inlined
- `GET /races/2024-bahrain` → results match real history exactly: Verstappen P1 (26.0 pts, win + fastest lap bonus), Perez P2 (18.0 pts), Sainz P3
- `GET /circuits/__nonexistent__` → correct 404

Full test suite passes (Codex also updated the stale 501-based test to expect 404, which was the right call).

## Frontend chunk 1 — ❌ blocked, not implemented

Gemini's dispatch hit `TerminalQuotaError: You have exhausted your daily quota` almost immediately — the free-tier `GEMINI_API_KEY` has very low per-metric limits (`limit: 5` and `limit: 20` requests/day observed on `gemini-3.5-flash`). It proposed an implementation plan but wrote **zero files** before exhausting quota (confirmed via `git status` — no changes in `frontend/`, no `frontend/app/races/` directory created).

This is a real constraint, not a one-off blip: the free API key tier is not viable for actual multi-step coding tasks (an agentic implementation loop — planning, tool calls, file writes, a subagent invocation, `tsc` verification — burns through single-digit-to-low-double-digit request budgets almost instantly).

## Decision needed

How to proceed on the Gemini side:
1. Wait for the daily quota to reset and retry (free, but frontend work stays blocked until then, and may hit the same wall again next attempt)
2. Enable billing on the Google AI Studio project backing this API key, for much higher paid-tier limits
3. Try Gemini's interactive Google-account login instead of an API key (a Gemini Advanced/AI Pro subscription may carry different quota than the raw free API key) — this was avoided earlier due to OAuth device-flow friction in this sandboxed shell, so may hit the same issue
4. Have Claude build the frontend chunks directly instead of dispatching to Gemini, at least for now

Not decided yet — flagged to the user.

## Files touched

- `backend/app/schemas/circuits.py`, `seasons.py`, `races.py` (new)
- `backend/app/api/v1/circuits.py`, `seasons.py`, `races.py` (implemented)
- `backend/tests/test_health.py` (updated 501→404 expectation)
- `backend/f1hub.db` (regenerated, gitignored, not committed)

## Next stage

Resolve the Gemini quota question, then continue with backend chunk 2 (standings) regardless — that track isn't blocked.
