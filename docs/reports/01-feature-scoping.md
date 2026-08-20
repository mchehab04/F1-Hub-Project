# Stage 01 — Feature scoping

**Date**: 2026-08-20
**Status**: Complete

## What was done

Ran a 3-agent chatroom debate (Product Strategist, ML/Data Engineer, Scope Skeptic — 2 rounds, early convergence at confidence 7-8/10) to scope and prioritize five candidate F1Hub features plus open-ended additions.

## Key decisions

- **Cut entirely**: live circuit dashboard — no free/official real-time F1 feed exists, and it's only demoable ~24 days a year. Replaced with a **historical race replay** (lap-by-lap position chart) reusing FastF1 session data already pulled for weather.
- **Deferred to v1.1+**: what-if mode (interactive prediction sliders) — "equal machinery" only becomes an honest feature once the model's trained and its sensitivities are known; the v1 feature schema is designed to be override-ready so this is additive later, not a rewrite. Also deferred: the race-week bulletin (real recurring content obligation, not a one-time build) and a "model vs. you" prediction game.
- **v1 model scope**: narrow grid→finish position model + an *independent* binary DNF classifier (not fused into one two-stage model) — simpler and faster to ship honestly, with an open disagreement (unresolved, left as a judgment call) on whether to later evolve toward a fused architecture.
- **Added**: a prediction-accuracy tracker (predicted vs. actual after every real GP) — proposed independently by all three agents, becomes the credibility mechanism for a deliberately narrow model.
- **Data sources locked**: Jolpica-F1 (Ergast successor — results/standings/calendar) + FastF1 (session weather + lap timing, ~2018+ usable window).

## Files created

- `.claude/skills/agent-chatrooms/active/chatroom/chat.json` — full debate transcript
- `.claude/skills/agent-chatrooms/active/chatroom/chatroom_report.md` — human-readable synthesis

## Next stage

Tech stack selection (see `02-tech-stack.md`).
