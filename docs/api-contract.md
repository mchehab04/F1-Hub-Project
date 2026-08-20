# F1Hub API Contract (v1 draft)

Status: **draft, pre-implementation**. This is the shared source of truth for the backend (FastAPI) and frontend (Next.js) agents until real code exists. Once the FastAPI app is running, `/openapi.json` / `/docs` becomes authoritative -- update this file if the implementation deviates, don't let them silently drift apart.

Scope: v1 features only, per `.claude/skills/agent-chatrooms/active/chatroom/chatroom_report.md` -- season overview, standings, prediction model + accuracy tracker, historical replay, head-to-head. What-if mode, the bulletin, and the "model vs. you" game are v1.1+ and deliberately excluded here, but see **Forward compatibility** at the bottom for how v1 shapes avoid boxing them out.

## Conventions

- Base path: `/api/v1`
- All IDs are stable string slugs, not raw DB integers -- reuses Jolpica-F1's existing `driverRef` / `constructorRef` / `circuitRef` conventions directly so the ETL doesn't need a translation layer.
  - `season`: integer year, e.g. `2026`
  - `race_id`: `{season}-{circuitRef}`, e.g. `"2026-bahrain"`
  - `driver_id`: Jolpica driverRef, e.g. `"verstappen"`, `"norris"`
  - `constructor_id`: Jolpica constructorRef, e.g. `"red_bull"`, `"mclaren"`
  - `circuit_id`: Jolpica circuitRef, e.g. `"bahrain"`, `"monza"`
- All timestamps are ISO 8601 UTC strings (`"2026-03-08T15:00:00Z"`). Exception: race `date` fields (e.g. `"2026-03-08"`) are intentionally date-only, not full timestamps -- session start times / a countdown feature are out of scope for v1.
- All field names are `snake_case` (matches Python/FastAPI defaults; Next.js side maps at the fetch layer, not by renegotiating the contract).
- Errors follow FastAPI's default shape: `{"detail": "<message>"}` with standard HTTP status codes (404 for missing resource, 422 for validation, 409 for state conflicts like "race hasn't happened yet").
- No auth in v1 (local-only, single user).

---

## Circuits

### `GET /api/v1/circuits/{circuit_id}`

```json
{
  "circuit_id": "bahrain",
  "name": "Bahrain International Circuit",
  "country": "Bahrain",
  "locality": "Sakhir",
  "length_km": 5.412,
  "laps": 57,
  "first_gp_year": 2004,
  "lap_record": { "time": "1:31.447", "driver_id": "hamilton", "year": 2005 },
  "technical_characteristic": {
    "downforce_level": "medium",
    "key_trait": "Long back straight rewards top speed, but the final sector is tight enough to punish a low-downforce setup."
  },
  "trivia": [
    "The only circuit to have hosted a Grand Prix under floodlights for its entire duration since 2014.",
    "Turn 1 is one of the most common first-lap incident spots on the calendar."
  ]
}
```

`lap_record` is `null` when the circuit is hosting its first-ever Grand Prix and no lap-time data exists yet.

`technical_characteristic` is static, editorial metadata (not derived from telemetry) describing the car setup trade-off the circuit rewards. `downforce_level` is one of `"low" | "medium" | "high"` (e.g. Monaco/Hungaroring are `"high"`; Baku/Las Vegas are `"low"`). This is descriptive context for the explainability panel — it gives a human-readable reason behind the `circuit_overtaking_difficulty` feature's importance score, not a new endpoint or model input. Deliberately out of scope: prescriptive setup-optimization advice (tire degradation, aero balance modeling) — that's a different, much larger modeling effort and isn't planned.

404 if `circuit_id` unknown.

---

## Season / Calendar

### `GET /api/v1/seasons`

List of seasons with browsable data.

```json
{ "seasons": [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026] }
```

### `GET /api/v1/seasons/{season}/races`

Race list for the season overview page.

```json
{
  "season": 2026,
  "races": [
    {
      "race_id": "2026-bahrain",
      "round": 1,
      "name": "Bahrain Grand Prix",
      "circuit_id": "bahrain",
      "circuit_name": "Bahrain International Circuit",
      "date": "2026-03-08",
      "status": "completed"
    },
    {
      "race_id": "2026-jeddah",
      "round": 2,
      "name": "Saudi Arabian Grand Prix",
      "circuit_id": "jeddah",
      "circuit_name": "Jeddah Corniche Circuit",
      "date": "2026-03-15",
      "status": "upcoming"
    }
  ]
}
```

`status` is one of `"upcoming" | "completed" | "postponed" | "cancelled"` -- drives whether the frontend shows a prediction view, a results-vs-prediction view, or a postponed/cancelled state.

### `GET /api/v1/races/{race_id}`

Single race detail, results included only if completed.

```json
{
  "race_id": "2026-bahrain",
  "round": 1,
  "season": 2026,
  "name": "Bahrain Grand Prix",
  "circuit_id": "bahrain",
  "date": "2026-03-08",
  "status": "completed",
  "results": [
    {
      "driver_id": "verstappen",
      "constructor_id": "red_bull",
      "constructor_name": "Red Bull Racing",
      "grid_position": 1,
      "finish_position": 1,
      "status": "finished",
      "points": 25
    },
    {
      "driver_id": "perez",
      "constructor_id": "red_bull",
      "constructor_name": "Red Bull Racing",
      "grid_position": 4,
      "finish_position": null,
      "status": "dnf",
      "points": 0
    }
  ]
}
```

`results` is `null`/omitted whenever `status != "completed"` (i.e. for `"upcoming"`, `"postponed"`, and `"cancelled"`). `status` per driver is `"finished" | "dnf" | "dsq" | "dns"`.

404 if `race_id` unknown.

---

## Prediction

### `GET /api/v1/races/{race_id}/prediction`

Works for any race -- upcoming (real prediction) or past (backtest). Returns 409 if the race's grid/weather inputs aren't available yet (e.g. requested before qualifying), or if the race is `"postponed"` or `"cancelled"` (detail message states which). Returns 404, not 409, for races before FastF1 coverage begins (pre-2018), since weather-derived inputs will never exist for those races -- distinct from the 409 used for "not yet available."

```json
{
  "race_id": "2026-jeddah",
  "model_version": "v1.0",
  "generated_at": "2026-03-14T09:00:00Z",
  "inputs": {
    "weather_category": "dry",
    "grid": [
      { "driver_id": "verstappen", "grid_position": 1, "constructor_id": "red_bull" }
    ],
    "derived_features": {
      "circuit_overtaking_difficulty": 0.63,
      "per_constructor": [
        { "constructor_id": "red_bull", "constructor_recent_form": 0.88, "constructor_reliability": 0.95 }
      ],
      "per_driver": [
        { "driver_id": "verstappen", "driver_circuit_history": 0.91, "driver_historical_dnf_rate": 0.04 }
      ]
    }
  },
  "predictions": [
    {
      "driver_id": "verstappen",
      "predicted_finish_position": 1,
      "dnf_probability": 0.04
    },
    {
      "driver_id": "perez",
      "predicted_finish_position": 5,
      "dnf_probability": 0.11
    }
  ]
}
```

- `predicted_finish_position` is the finish-position model's output (only meaningful conditional on not-DNF; the frontend should present these as two separate signals, not multiply them together).
- `inputs` echoes back every feature value actually used, including the model's derived/engineered features under `derived_features` -- this is what makes the response forward-compatible with what-if mode later (see bottom).

---

## Model

### `GET /api/v1/models/{model_version}/explain`

Feature importance for the trained model -- powers the explainability panel. `feature_importances_` (scikit-learn) is a global property of the trained model, not of any individual race, so this is model-scoped rather than nested under `/races/{race_id}/`; the values are the same regardless of which race you're looking at.

```json
{
  "model_version": "v1.0",
  "finish_position_model": {
    "feature_importances": [
      { "feature": "grid_position", "importance": 0.52 },
      { "feature": "constructor_recent_form", "importance": 0.24 },
      { "feature": "circuit_overtaking_difficulty", "importance": 0.11 },
      { "feature": "weather_category", "importance": 0.08 },
      { "feature": "driver_circuit_history", "importance": 0.05 }
    ]
  },
  "dnf_model": {
    "feature_importances": [
      { "feature": "driver_historical_dnf_rate", "importance": 0.41 },
      { "feature": "constructor_reliability", "importance": 0.35 },
      { "feature": "weather_category", "importance": 0.24 }
    ]
  }
}
```

404 if `model_version` unknown.

---

## Accuracy tracker

### `GET /api/v1/races/{race_id}/accuracy`

Only valid once a race is `"completed"` **and** a prediction was generated for it beforehand (i.e., not a race predicted after the fact). Returns the same 409 shape as `GET /prediction` (`{"detail": "<message>"}`) when no prediction exists yet for this race; this also covers `"postponed"`/`"cancelled"` races automatically, since they can never become `"completed"`.

```json
{
  "race_id": "2026-bahrain",
  "model_version": "v1.0",
  "per_driver": [
    {
      "driver_id": "verstappen",
      "predicted_finish_position": 1,
      "actual_finish_position": 1,
      "actual_status": "finished",
      "position_error": 0
    },
    {
      "driver_id": "perez",
      "predicted_finish_position": 5,
      "actual_finish_position": null,
      "actual_status": "dnf",
      "position_error": null
    }
  ],
  "summary": {
    "mean_absolute_position_error": 2.3,
    "dnf_brier_score": 0.14,
    "rank_correlation": 0.81,
    "podium_hit_rate": 0.67
  }
}
```

`actual_status` is always present on every `per_driver` entry, using the same enum as race results (`"finished" | "dnf" | "dsq" | "dns"`).

`mean_absolute_position_error` alone can undersell a model that's directionally right but rarely exact (e.g. every driver off by one position gives MAE `1.0`, not "0% accuracy") -- `rank_correlation` (Spearman's rho between predicted and actual order, DNFs placed last) makes that "close but not exact" case visibly score well, and `podium_hit_rate` is the plain-language headline number for a non-technical visitor glancing at the page: `podium_hit_rate = |predicted_top_3 ∩ actual_top_3| / 3`, where `predicted_top_3` is the three drivers with the lowest `predicted_finish_position` and `actual_top_3` is the three drivers with the lowest `actual_finish_position` (an order-independent set overlap, not an exact-order match).

### `GET /api/v1/seasons/{season}/accuracy`

Running accuracy trend across the season -- powers the season-level accuracy chart.

```json
{
  "season": 2026,
  "races": [
    { "race_id": "2026-bahrain", "round": 1, "mean_absolute_position_error": 2.3, "dnf_brier_score": 0.14, "rank_correlation": 0.81, "podium_hit_rate": 0.67 },
    { "race_id": "2026-jeddah", "round": 2, "mean_absolute_position_error": 1.9, "dnf_brier_score": 0.09, "rank_correlation": 0.85, "podium_hit_rate": 1.0 }
  ],
  "season_running_average": {
    "mean_absolute_position_error": 2.1,
    "dnf_brier_score": 0.115,
    "rank_correlation": 0.83,
    "podium_hit_rate": 0.835
  }
}
```

---

## Standings

### `GET /api/v1/standings/drivers?season=2026`

```json
{
  "season": 2026,
  "as_of_round": 2,
  "standings": [
    {
      "driver_id": "verstappen",
      "constructor_id": "red_bull",
      "constructor_name": "Red Bull Racing",
      "position": 1,
      "points": 44,
      "wins": 2,
      "podiums": 2,
      "trend": [25, 19]
    }
  ]
}
```

`trend` is points-per-race for every completed race in the requested season so far, in chronological order; its length always equals `as_of_round`. Feeds a sparkline.

If a driver changed constructors mid-season, `constructor_id`/`constructor_name` reflect their most recent constructor as of `as_of_round`; `points`, `wins`, and `podiums` are summed across all constructors driven for that season (matches real-world F1 convention).

### `GET /api/v1/standings/constructors?season=2026`

Same shape, `constructor_id` + aggregated team points instead of `driver_id`.

---

## Drivers

### `GET /api/v1/drivers/{driver_id}`

```json
{
  "driver_id": "verstappen",
  "name": "Max Verstappen",
  "nationality": "Dutch",
  "date_of_birth": "1997-09-30",
  "current_constructor_id": "red_bull",
  "career": { "wins": 63, "podiums": 112, "poles": 40, "championships": 4 }
}
```

### `GET /api/v1/drivers/compare?driver_a=verstappen&driver_b=norris&season=2026`

Head-to-head, scoped to a season (defaults to career if `season` omitted).

```json
{
  "driver_a": "verstappen",
  "driver_b": "norris",
  "season": 2026,
  "head_to_head": {
    "qualifying_wins": { "verstappen": 5, "norris": 3 },
    "race_finish_wins": { "verstappen": 6, "norris": 2 },
    "points": { "verstappen": 180, "norris": 142 }
  }
}
```

If either driver did not race in the requested `season`, returns 404: `{"detail": "driver <id> did not race in season <year>"}`.

---

## Constructors

### `GET /api/v1/constructors/{constructor_id}`

```json
{
  "constructor_id": "red_bull",
  "name": "Red Bull Racing",
  "nationality": "Austrian",
  "current_drivers": ["verstappen", "perez"],
  "career": { "wins": 118, "podiums": 300, "poles": 100, "championships": 6 }
}
```

404 if `constructor_id` unknown.

### `GET /api/v1/constructors/compare?constructor_a=red_bull&constructor_b=mclaren&season=2026`

Team head-to-head, mirroring driver compare. Scoped to a season (defaults to career if `season` omitted).

```json
{
  "constructor_a": "red_bull",
  "constructor_b": "mclaren",
  "season": 2026,
  "head_to_head": {
    "race_wins": { "red_bull": 6, "mclaren": 2 },
    "points": { "red_bull": 350, "mclaren": 240 },
    "podiums": { "red_bull": 10, "mclaren": 4 }
  }
}
```

If either constructor did not compete in the requested `season`, returns 404: `{"detail": "constructor <id> did not compete in season <year>"}`.

---

## Replay

### `GET /api/v1/races/{race_id}/replay`

Only valid for `"completed"` races. This is FastF1 session data reused directly -- no separate pipeline. Returns 404, not 409, for races before FastF1 coverage begins (pre-2018), since no session data will ever exist for that period -- distinct from the 409 used elsewhere for "not yet available."

```json
{
  "race_id": "2026-bahrain",
  "total_laps": 57,
  "drivers": [
    {
      "driver_id": "verstappen",
      "laps": [
        { "lap": 1, "position": 1, "gap_to_leader_s": 0.0 },
        { "lap": 2, "position": 1, "gap_to_leader_s": 0.0 }
      ]
    }
  ]
}
```

For a driver who DNFs, `laps` truncates at their last completed lap -- that driver's array will be shorter than `total_laps`, and the frontend must not assume uniform array length across drivers. `gap_to_leader_s` is the sole gap signal in v1 (no separate `laps_down` field); once a driver has been lapped, this value can exceed one lap's time.

Payload for a full race (~20 drivers x ~60 laps x small record) is small enough to return in one response -- no pagination needed in v1.

---

## Forward compatibility (v1.1+, not built yet)

The `inputs` block on `GET /races/{race_id}/prediction` -- including its `derived_features` sub-block -- is the seam that lets what-if mode land in v1.1 without a v1 rewrite: a future `POST /api/v1/races/{race_id}/prediction/simulate` can accept an overridden version of that same `inputs` shape (different `weather_category`, adjusted `grid`, overridden `derived_features` like `constructor_recent_form` or `driver_historical_dnf_rate`) and return the same `predictions` shape back. Because `derived_features` now enumerates every feature used by both the finish-position and DNF models (see **Model** section), the schema is genuinely override-ready today, not just in name. Keep feature names and the `inputs` structure stable now so that endpoint is additive later, not a breaking change.
