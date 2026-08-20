"""Load race-session weather and replay lap data from FastF1."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.db.tables import Driver, Race, RaceEntry, RaceStatus, ReplayLap, SessionWeather

FASTF1_MIN_SEASON = 2018
FASTF1_SESSION_NAME = "R"


@dataclass
class FastF1LoadResult:
    races_attempted: int = 0
    weather_rows_loaded: int = 0
    replay_laps_loaded: int = 0
    data_issues: list[str] = field(default_factory=list)


def load_fastf1_data(
    db: Session,
    start_season: int,
    end_season: int,
    cache_dir: Path | str = Path("data/cache"),
) -> FastF1LoadResult:
    import fastf1

    result = FastF1LoadResult()
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_path))

    races = (
        db.query(Race)
        .filter(
            Race.season >= max(start_season, FASTF1_MIN_SEASON),
            Race.season <= end_season,
            Race.status == RaceStatus.COMPLETED.value,
        )
        .order_by(Race.season, Race.round)
        .all()
    )

    for race in races:
        result.races_attempted += 1
        try:
            session = fastf1.get_session(race.season, race.round, FASTF1_SESSION_NAME)
            _load_session(session)
        except Exception as exc:  # FastF1 raises a mix of transport/parser errors.
            result.data_issues.append(f"{race.race_id}: FastF1 session load failed ({exc})")
            db.rollback()
            continue

        try:
            weather_loaded = _upsert_weather(db, race.race_id, session.weather_data)
            replay_loaded, issues = _replace_replay_laps(db, race.race_id, session)
            result.weather_rows_loaded += int(weather_loaded)
            result.replay_laps_loaded += replay_loaded
            result.data_issues.extend(f"{race.race_id}: {issue}" for issue in issues)
            db.commit()
        except Exception as exc:
            result.data_issues.append(f"{race.race_id}: FastF1 transform failed ({exc})")
            db.rollback()

    return result


def _load_session(session: Any) -> None:
    try:
        session.load(laps=True, telemetry=False, weather=True, messages=False)
    except TypeError:
        session.load()


def _upsert_weather(db: Session, race_id: str, weather_data: pd.DataFrame | None) -> bool:
    if weather_data is None or weather_data.empty:
        weather_category = "unknown"
        air_temp = track_temp = humidity = rainfall = None
    else:
        rainfall_series = _truthy_series(weather_data.get("Rainfall"))
        rainfall = bool(rainfall_series.any()) if rainfall_series is not None else None
        weather_category = _weather_category(rainfall_series)
        air_temp = _mean_or_none(weather_data.get("AirTemp"))
        track_temp = _mean_or_none(weather_data.get("TrackTemp"))
        humidity = _mean_or_none(weather_data.get("Humidity"))

    row = db.get(SessionWeather, race_id)
    if row is None:
        row = SessionWeather(race_id=race_id, weather_category=weather_category)
        db.add(row)

    row.weather_category = weather_category
    row.air_temp_c = air_temp
    row.track_temp_c = track_temp
    row.humidity_pct = humidity
    row.rainfall = rainfall
    return True


def _replace_replay_laps(db: Session, race_id: str, session: Any) -> tuple[int, list[str]]:
    issues: list[str] = []
    db.query(ReplayLap).filter(ReplayLap.race_id == race_id).delete(synchronize_session=False)

    laps = session.laps
    if laps is None or laps.empty:
        return 0, ["no FastF1 lap data"]

    driver_map, mapping_issues = _driver_code_to_jolpica_id(db, race_id, session)
    issues.extend(mapping_issues)

    required_columns = {"Driver", "LapNumber", "Position", "Time"}
    missing_columns = required_columns.difference(set(laps.columns))
    if missing_columns:
        return 0, [f"lap data missing columns: {sorted(missing_columns)}"]

    clean_laps = laps.dropna(subset=["Driver", "LapNumber", "Position", "Time"]).copy()
    if clean_laps.empty:
        return 0, ["lap data empty after dropping incomplete rows"]

    clean_laps["LapNumber"] = clean_laps["LapNumber"].astype(int)
    clean_laps["Position"] = clean_laps["Position"].astype(int)
    leader_times = clean_laps.groupby("LapNumber")["Time"].min()

    rows: list[ReplayLap] = []
    unmapped_codes: set[str] = set()
    for lap in clean_laps.itertuples(index=False):
        driver_code = str(getattr(lap, "Driver"))
        driver_id = driver_map.get(driver_code)
        if driver_id is None:
            unmapped_codes.add(driver_code)
            continue

        lap_number = int(getattr(lap, "LapNumber"))
        leader_time = leader_times.get(lap_number)
        if pd.isna(leader_time):
            continue
        gap = (getattr(lap, "Time") - leader_time).total_seconds()
        rows.append(
            ReplayLap(
                race_id=race_id,
                driver_id=driver_id,
                lap=lap_number,
                position=int(getattr(lap, "Position")),
                gap_to_leader_s=max(0.0, float(gap)),
            )
        )

    if unmapped_codes:
        issues.append(f"unmapped FastF1 driver codes skipped: {sorted(unmapped_codes)}")
    if rows:
        db.bulk_save_objects(rows)
    return len(rows), issues


def _driver_code_to_jolpica_id(
    db: Session, race_id: str, session: Any
) -> tuple[dict[str, str], list[str]]:
    issues: list[str] = []
    jolpica_drivers = _jolpica_drivers_for_race(db, race_id)
    by_name = {_normalize_name(driver.name): driver.driver_id for driver in jolpica_drivers}
    by_family = {
        _normalize_name(driver.name.split()[-1]): driver.driver_id
        for driver in jolpica_drivers
        if driver.name
    }
    by_id = {driver.driver_id: driver.driver_id for driver in jolpica_drivers}

    results = getattr(session, "results", None)
    if results is None or results.empty:
        issues.append("FastF1 results table unavailable; falling back to lap driver codes")
        return _fallback_code_map(jolpica_drivers), issues

    mapping: dict[str, str] = {}
    for row in results.itertuples(index=False):
        code = _row_value(row, "Abbreviation")
        if not code:
            continue

        candidates = [
            _normalize_name(_row_value(row, "FullName")),
            _normalize_name(
                f"{_row_value(row, 'FirstName') or ''} {_row_value(row, 'LastName') or ''}"
            ),
            _normalize_name(_row_value(row, "LastName")),
            _normalize_driver_id(_row_value(row, "DriverId")),
        ]
        driver_id = _first_match(candidates, by_name, by_family, by_id)
        if driver_id is None:
            issues.append(f"could not map FastF1 driver {code} ({candidates}) to Jolpica ID")
            continue
        mapping[str(code)] = driver_id

    if not mapping:
        issues.append("FastF1 results mapping empty; falling back to lap driver codes")
        mapping = _fallback_code_map(jolpica_drivers)
    return mapping, issues


def _jolpica_drivers_for_race(db: Session, race_id: str) -> list[Driver]:
    return (
        db.query(Driver)
        .join(RaceEntry, Driver.driver_id == RaceEntry.driver_id)
        .filter(RaceEntry.race_id == race_id)
        .all()
    )


def _fallback_code_map(drivers: list[Driver]) -> dict[str, str]:
    return {driver.driver_id[:3].upper(): driver.driver_id for driver in drivers}


def _first_match(
    candidates: list[str], by_name: dict[str, str], by_family: dict[str, str], by_id: dict[str, str]
) -> str | None:
    for candidate in candidates:
        if not candidate:
            continue
        if candidate in by_name:
            return by_name[candidate]
        if candidate in by_family:
            return by_family[candidate]
        if candidate in by_id:
            return by_id[candidate]
        if "_" in candidate:
            family = candidate.rsplit("_", 1)[-1]
            if family in by_family or family in by_id:
                return by_family.get(family) or by_id.get(family)
    return None


def _normalize_name(value: Any) -> str:
    if not value:
        return ""
    ascii_value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return (
        ascii_value
        .lower()
        .replace(".", "")
        .replace("-", " ")
        .replace("_", " ")
        .strip()
    )


def _normalize_driver_id(value: Any) -> str:
    return _normalize_name(value).replace(" ", "_")


def _row_value(row: Any, name: str) -> Any:
    return getattr(row, name, None)


def _mean_or_none(series: pd.Series | None) -> float | None:
    if series is None:
        return None
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return None
    return float(numeric.mean())


def _truthy_series(series: pd.Series | None) -> pd.Series | None:
    if series is None:
        return None
    return series.dropna().astype(bool)


def _weather_category(rainfall_series: pd.Series | None) -> str:
    if rainfall_series is None or rainfall_series.empty:
        return "unknown"
    rain_ratio = float(rainfall_series.mean())
    if rain_ratio == 0:
        return "dry"
    if rain_ratio == 1:
        return "wet"
    return "mixed"
