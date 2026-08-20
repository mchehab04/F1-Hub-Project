# F1Hub SQLite schema design

Status: **draft, implemented** in `backend/app/db/tables.py`. Companion to `docs/api-contract.md` — every table here exists to serve one or more contract endpoints; nothing here is speculative.

## Design principles

1. **Relational where data is queried granularly or grows large; JSON where it's always read/written as one unit.** Race results and lap-by-lap replay data are genuinely tabular and get aggregated (standings, accuracy metrics) — real tables. A prediction's `inputs`/`predictions` payload and a model's feature-importance list are always fetched and stored whole, never queried by a sub-field — JSON columns, to avoid four extra join tables for data with no relational access pattern.
2. **No dedicated `seasons` or `standings` tables.** Seasons are `SELECT DISTINCT season FROM races`; standings are aggregated from `race_entries` at query time (join to `races` for season/round filtering). SQLite handles this fine at hobby-project scale, and it avoids a cache-invalidation problem — a materialized standings table would need to stay in sync with `race_entries` on every ETL write, which is complexity this project doesn't need yet.
3. **ETL populates precomputed career stats.** `career_wins/podiums/poles/championships` on `drivers`/`constructors` are written by the ETL step from Jolpica's full historical data, not computed on the fly — multi-season aggregation on every `GET /drivers/{id}` call is wasted work for data that only changes once a race weekend.
4. **Field names mirror the API contract 1:1** wherever the shape allows, so the FastAPI layer is a thin translation, not a redesign. The one deliberate exception: `circuits.lap_record` is decomposed into `lap_record_time` / `lap_record_driver_id` / `lap_record_year` (all nullable together) — the API layer reassembles these into the nested `lap_record` object, or `null` if `lap_record_time IS NULL`.

## Tables

### `constructors`
| Column | Type | Notes |
|---|---|---|
| `constructor_id` | TEXT PK | Jolpica `constructorRef` slug |
| `name`, `nationality` | TEXT | |
| `career_wins/podiums/poles/championships` | INTEGER | ETL-populated |

### `drivers`
| Column | Type | Notes |
|---|---|---|
| `driver_id` | TEXT PK | Jolpica `driverRef` slug |
| `name`, `nationality` | TEXT | |
| `date_of_birth` | DATE | |
| `current_constructor_id` | TEXT FK → constructors, nullable | |
| `career_wins/podiums/poles/championships` | INTEGER | ETL-populated |

`GET /constructors/{id}`'s `current_drivers` list is a reverse query (`WHERE current_constructor_id = ?`), not a stored column — avoids denormalized state that can drift.

### `circuits`
| Column | Type | Notes |
|---|---|---|
| `circuit_id` | TEXT PK | Jolpica `circuitRef` slug |
| `name`, `country`, `locality` | TEXT | |
| `length_km` | REAL | |
| `laps` | INTEGER | Standard/scheduled lap count |
| `first_gp_year` | INTEGER | |
| `lap_record_time` | TEXT, nullable | e.g. `"1:31.447"` |
| `lap_record_driver_id` | TEXT FK → drivers, nullable | |
| `lap_record_year` | INTEGER, nullable | |
| `downforce_level` | TEXT, nullable | `low`\|`medium`\|`high` |
| `key_trait` | TEXT, nullable | Free-text setup-tradeoff sentence |
| `trivia` | JSON (list[str]) | Small, always read/written whole |

### `races`
| Column | Type | Notes |
|---|---|---|
| `race_id` | TEXT PK | `{season}-{circuitRef}` |
| `season`, `round` | INTEGER | `UNIQUE(season, round)` |
| `name` | TEXT | |
| `circuit_id` | TEXT FK → circuits | |
| `date` | DATE | |
| `status` | TEXT | `upcoming`\|`completed`\|`postponed`\|`cancelled`, CHECK-constrained |
| `total_laps` | INTEGER, nullable | Actual laps run/scheduled — feeds `replay.total_laps` |

### `race_entries`
One row per driver per race — the workhorse table: race results, standings aggregation, and actual values for the accuracy tracker all read from here.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `race_id` | TEXT FK → races | |
| `driver_id` | TEXT FK → drivers | |
| `constructor_id` | TEXT FK → constructors | Team driven for **at that race** — makes mid-season transfers fall out naturally; standings sum points across whichever constructor rows exist per driver per season |
| `grid_position` | INTEGER, nullable | Null before qualifying |
| `finish_position` | INTEGER, nullable | Null if DNF/DSQ/DNS or not yet run |
| `status` | TEXT, nullable | `finished`\|`dnf`\|`dsq`\|`dns`, CHECK-constrained, null until race is run |
| `points` | REAL | Default 0 |

`UNIQUE(race_id, driver_id)`. Indexed on `driver_id` and `constructor_id` for standings/head-to-head queries.

### `session_weather`
One row per race (v1 only needs race-session weather, not every session).

| Column | Type | Notes |
|---|---|---|
| `race_id` | TEXT PK/FK → races | |
| `weather_category` | TEXT | Matches the prediction `inputs.weather_category` value |
| `air_temp_c`, `track_temp_c`, `humidity_pct` | REAL, nullable | Raw FastF1 telemetry, for future feature engineering |
| `rainfall` | BOOLEAN, nullable | |

### `replay_laps`
One row per driver per lap per race — FastF1 lap-by-lap data, reused directly for the replay endpoint.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `race_id` | TEXT FK → races | Indexed |
| `driver_id` | TEXT FK → drivers | |
| `lap` | INTEGER | |
| `position` | INTEGER | |
| `gap_to_leader_s` | REAL | |

`UNIQUE(race_id, driver_id, lap)`. A DNF'd driver simply has fewer rows than `races.total_laps` — matches the contract's documented truncation behavior, no explicit "DNF lap" marker needed.

### `model_versions`
| Column | Type | Notes |
|---|---|---|
| `model_version` | TEXT PK | e.g. `"v1.0"` |
| `created_at` | DATETIME | |
| `finish_position_feature_importances` | JSON (list of `{feature, importance}`) | Backs `/models/{version}/explain` |
| `dnf_feature_importances` | JSON (list of `{feature, importance}`) | |

### `predictions`
| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `race_id` | TEXT FK → races | |
| `model_version` | TEXT FK → model_versions | |
| `generated_at` | DATETIME | |
| `inputs` | JSON | The full `inputs` object from the contract, incl. `derived_features` |
| `predictions` | JSON | The full `predictions` array |

`UNIQUE(race_id, model_version)` — one prediction per race per model version. The accuracy tracker joins this against `race_entries` for the same `race_id` to compute `mean_absolute_position_error`, `dnf_brier_score`, `rank_correlation`, and `podium_hit_rate` at query time (or as a batch job after each race — either is fine at this data volume; not decided yet, left to the `ml/evaluate.py` implementation).

## What's deliberately not modeled yet

- No migrations tool (Alembic, etc.) — for a solo local-only v1, `Base.metadata.create_all()` at startup is enough. Revisit if the schema needs to evolve after real data exists.
- No `what_if_simulations` table — v1.1+ scope per the chatroom report; the `predictions.inputs` JSON shape is already the seam that makes this additive later.
