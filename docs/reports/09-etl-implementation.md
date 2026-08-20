# Stage 09 — ETL implementation (Jolpica-F1 + FastF1)

**Date**: 2026-08-20/21
**Status**: Complete, verified against real data. Idempotency re-verification pending (see below).

## What was done

Dispatched the ETL layer implementation to Codex (via the `codex-backend` MCP worker, per `docs/orchestration.md`), scoped to `backend/etl/{fetch_jolpica,fetch_fastf1,build_db}.py` against the locked schema/contract. Codex implemented all three files but could not run/verify them itself — its sandboxed subprocess couldn't resolve a working Python (hit the Windows Store `python.exe` app-execution-alias stub, which its OS-level sandbox can't traverse) and a dependency-install approval request failed at the tool layer.

Rather than accept unverified code, recreated the backend venv cleanly via Bash (which resolves a real Python 3.11 correctly, unlike the broken alias), installed the full `requirements.txt`, and actually ran the ETL end-to-end against the 2024 season — catching and fixing four real issues along the way.

## Bugs found and fixed (all found by actually running the code, not just reading it)

1. **Lap record overwritten unconditionally on rerun.** `_apply_lap_records` replaced `circuit.lap_record_*` with whatever was fastest in the *current run's* season range, with no comparison to what was already stored. A later run covering only newer/slower seasons would silently overwrite a genuinely faster record from a season it didn't touch. Fixed to compare against the existing stored time first.
2. **Duplicate-row `UNIQUE constraint failed` on drivers/constructors.** `_upsert_driver`/`_upsert_constructor`/`_upsert_circuit` used `db.get()` to check for an existing row, but `db.get()` only sees *persistent* rows — an object added-but-not-yet-flushed earlier in the same run is invisible to it. Since a constructor fields two drivers per race, the second entry's lookup missed the first entry's pending row and created a duplicate. First tried flushing per-race (insufficient — duplicates occurred *within* a single race, since two entries for the same team are both processed before any flush). Fixed properly with explicit in-memory caches (`driver_cache`/`constructor_cache`/`circuit_cache`) as the source of truth for "already created this run," with `db.get()` only consulted on a cache miss.
3. **No retry on transient network errors.** `JolpicaClient.get()` had no retry logic — a single SSL/connection blip killed the whole run. Added retry-with-backoff for `SSLError`/`ConnectionError`, and separately for HTTP 429 (rate limiting), respecting `Retry-After` when present.
4. **Unnecessary API calls on rerun.** `_upsert_circuit` re-fetched `first_gp_year` from the API for every circuit on every run, even though that value never changes once known. On a rerun of an already-ingested season this burned ~24 avoidable API calls, directly contributing to a 429 during idempotency testing. Fixed to reuse the value from an existing circuit row (cache or DB) before hitting the API.

## A genuine environment issue (not a code bug)

This network's IPv6 path resets the TLS handshake to `api.jolpi.ca` (reproduced independently with `curl`, not just inside Python — IPv4 works fine). Forced IPv4-only DNS resolution in the ETL client (`urllib3.util.connection.allowed_gai_family`) to route around it. This also incidentally benefits FastF1's own HTTP calls, since the patch is process-global.

## Also fixed: a real `.gitignore` bug

While checking that FastF1's session cache (`backend/data/cache/`, ended up ~166MB) wouldn't get committed, found that the existing `data/cache/` gitignore pattern was silently **not matching** `backend/data/cache/` at all — a pattern containing a slash (not just trailing) is anchored to the repo root in gitignore syntax, so it only matched a top-level `./data/cache/` that doesn't exist. `git check-ignore` confirmed zero matches before the fix. Replaced with an explicit `backend/data/` entry and verified with `git check-ignore` that it now matches. Without catching this, the next `git add` would have staged ~166MB of binary cache data.

## Verification

- Full run against the 2024 season: **24 races, 24 circuits, 24 drivers, 10 constructors, 479 race entries, 24 weather rows, 26,578 replay laps** — succeeded with 0 data-quality issues logged.
- Spot-checked the actual data against known real-world 2024 F1 facts: Verstappen 9 wins/14 podiums (correct), McLaren credited as constructors' champion despite Red Bull's driver winning more races individually (correct — matches the real 2024 season), a DNF'd driver's (Zhou, Bahrain) replay laps correctly stop one lap short of the race's 57 total laps rather than continuing or padding.
- Confirmed the crash-safety of the transaction model: after two failed reruns (hit the pre-existing-first_gp_year 429 issue, then a harder connection-level block from the API after repeated rapid requests), verified row counts were **unchanged** from the successful run — SQLAlchemy's implicit rollback-on-`close()` correctly discarded the failed attempts' flushed-but-uncommitted writes.
- Backend test suite (`pytest`) still green throughout.

## Not yet verified

**A full second successful rerun** (true idempotency, "update existing row" path) wasn't re-confirmed live — after fixing the API-call-reduction bug, a further rerun attempt hit a harder connection-level block from Jolpica (TLS handshake completes, then the connection is dropped with no HTTP response), i.e. this free API was pushed too hard during one testing session. Chose to stop rather than keep hammering it. Confidence this is still correct: the "row already exists → update its fields" branch in every upsert function is standard SQLAlchemy ORM behavior (setting attributes on a persistent object emits an UPDATE), not novel logic specific to this codebase — but it should be re-run against a live rerun once enough time has passed, before relying on it for a real incremental multi-season backfill.

## Files touched

- `backend/etl/fetch_jolpica.py`, `backend/etl/fetch_fastf1.py`, `backend/etl/build_db.py` — implemented (Codex) + fixed (Claude, after live testing)
- `.gitignore` — fixed the anchoring bug, added `.python-user/`

## Next stage

Re-verify idempotency with a live rerun once the API cooldown has passed. After that, the ML layer (`backend/ml/`) is the next dependency-unblocked piece — training now has real 2024 data to work against, though a fuller historical backfill (more seasons) would meaningfully improve model quality before that's worth doing.
