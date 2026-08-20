"""Load calendar, result, and entrant data from the Jolpica-F1 API.

Jolpica is an Ergast-compatible API. Its documented base route is:
https://api.jolpi.ca/ergast/f1/
"""

from __future__ import annotations

import socket
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import requests
import urllib3.util.connection as urllib3_connection
from sqlalchemy.orm import Session

from app.db.tables import (
    Circuit,
    Constructor,
    Driver,
    DriverResultStatus,
    Race,
    RaceEntry,
    RaceStatus,
)

JOLPICA_BASE_URL = "https://api.jolpi.ca/ergast/f1"
USER_AGENT = "F1HubETL/0.1 (https://github.com/local/f1hub)"

# This dev network's IPv6 path resets the TLS handshake to api.jolpi.ca
# (reproduced with curl outside Python too -- IPv4 works fine, IPv6 doesn't).
# Force IPv4-only DNS resolution so requests doesn't keep trying the broken
# IPv6 route first. Safe/inert on networks where IPv6 works normally.
urllib3_connection.allowed_gai_family = lambda: socket.AF_INET

# Jolpica/Ergast circuit objects do not include circuit length. The database
# column is currently non-nullable, so ETL keeps factual known lengths here and
# writes 0.0 only for unknown historical circuits, reporting that as a data issue.
CIRCUIT_LENGTH_KM: dict[str, float] = {
    "adelaide": 3.780,
    "ain-diab": 7.618,
    "aintree": 4.828,
    "albert_park": 5.278,
    "americas": 5.513,
    "anderstorp": 4.031,
    "avus": 8.300,
    "bahrain": 5.412,
    "baku": 6.003,
    "boavista": 7.775,
    "brands_hatch": 4.207,
    "bremgarten": 7.280,
    "buddh": 5.125,
    "catalunya": 4.657,
    "charade": 8.055,
    "dallas": 3.901,
    "detroit": 4.023,
    "dijon": 3.801,
    "donington": 4.023,
    "essarts": 6.542,
    "estoril": 4.360,
    "fuji": 4.563,
    "galvez": 4.259,
    "george": 3.920,
    "hockenheimring": 4.574,
    "hungaroring": 4.381,
    "imola": 4.909,
    "indianapolis": 4.192,
    "interlagos": 4.309,
    "istanbul": 5.338,
    "jacarepagua": 5.031,
    "jarama": 3.404,
    "jeddah": 6.174,
    "jerez": 4.428,
    "kyalami": 4.261,
    "las_vegas": 6.201,
    "lemans": 13.626,
    "long_beach": 3.275,
    "losail": 5.419,
    "magny_cours": 4.411,
    "marina_bay": 4.940,
    "miami": 5.412,
    "monaco": 3.337,
    "monsanto": 5.440,
    "montjuic": 3.791,
    "monza": 5.793,
    "mosport": 3.957,
    "mugello": 5.245,
    "nivelles": 3.724,
    "nurburgring": 5.148,
    "okayama": 3.703,
    "pedralbes": 6.316,
    "pescara": 25.579,
    "phoenix": 3.721,
    "portimao": 4.653,
    "red_bull_ring": 4.318,
    "reims": 8.302,
    "ricard": 5.842,
    "riverside": 5.271,
    "rodriguez": 4.304,
    "rouen": 6.542,
    "sepang": 5.543,
    "sebring": 8.356,
    "shanghai": 5.451,
    "silverstone": 5.891,
    "sochi": 5.848,
    "spa": 7.004,
    "suzuka": 5.807,
    "tremblant": 4.265,
    "valencia": 5.419,
    "vegas": 6.201,
    "villeneuve": 4.361,
    "watkins_glen": 5.435,
    "yas_marina": 5.281,
    "yeongam": 5.615,
    "zandvoort": 4.259,
    "zeltweg": 3.186,
    "zolder": 4.262,
}


@dataclass
class JolpicaLoadResult:
    seasons: list[int]
    races_loaded: int = 0
    race_entries_loaded: int = 0
    data_issues: list[str] = field(default_factory=list)


class JolpicaClient:
    def __init__(self, base_url: str = JOLPICA_BASE_URL, max_retries: int = 4) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.max_retries = max_retries

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/{path.strip('/')}/"
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code == 429:
                    # Rate limited -- respect Retry-After if the server sent
                    # one, otherwise back off. Observed in practice when
                    # re-running the ETL shortly after a full-season pull.
                    retry_after = response.headers.get("Retry-After")
                    wait = float(retry_after) if retry_after else 2**attempt * 2
                    last_exc = requests.exceptions.HTTPError(
                        f"429 rate limited on {url}", response=response
                    )
                    if attempt + 1 < self.max_retries:
                        time.sleep(wait)
                        continue
                    raise last_exc
                response.raise_for_status()
                time.sleep(0.15)
                return response.json()["MRData"]
            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as exc:
                # This network is prone to transient TLS/connection resets
                # (observed during ETL dependency install too) -- retry with
                # backoff rather than failing the whole run on one blip.
                last_exc = exc
                if attempt + 1 < self.max_retries:
                    time.sleep(2**attempt)
        assert last_exc is not None
        raise last_exc

    def race_table(self, path: str) -> list[dict[str, Any]]:
        races: list[dict[str, Any]] = []
        offset = 0
        total: int | None = None

        while total is None or offset < total:
            data = self.get(path, {"limit": 100, "offset": offset})
            total = int(data.get("total", 0))
            limit = int(data.get("limit", 100))
            races.extend(data.get("RaceTable", {}).get("Races", []))
            if limit <= 0:
                break
            offset += limit

        return races


def load_jolpica_data(
    db: Session, start_season: int, end_season: int, client: JolpicaClient | None = None
) -> JolpicaLoadResult:
    client = client or JolpicaClient()
    result = JolpicaLoadResult(seasons=list(range(start_season, end_season + 1)))

    driver_stats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    constructor_stats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    driver_points_by_season: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    constructor_points_by_season: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    latest_constructor_by_driver: dict[str, tuple[int, int, str]] = {}
    first_gp_year_by_circuit: dict[str, int] = {}
    fastest_lap_by_circuit: dict[str, tuple[float, str, str, int]] = {}

    # db.get() only sees PERSISTENT rows -- an object added-but-not-yet-
    # flushed in this same run is invisible to it. A constructor fields two
    # drivers per race, so without this cache the second entry's db.get()
    # would miss the first entry's just-added-but-unflushed row and create a
    # duplicate. Cache is the source of truth for "already created this run";
    # db.get() is only consulted on cache miss (to pick up prior ETL runs).
    driver_cache: dict[str, Driver] = {}
    constructor_cache: dict[str, Constructor] = {}
    circuit_cache: dict[str, Circuit] = {}

    for season in range(start_season, end_season + 1):
        races = client.race_table(f"{season}/races")
        poles_by_round = _fetch_poles_by_round(client, season, result)

        for calendar_race in races:
            round_number = int(calendar_race["round"])
            race_results = client.race_table(f"{season}/{round_number}/results")
            result_race = race_results[0] if race_results else calendar_race
            entries = result_race.get("Results", [])
            race_id = _race_id(result_race)

            circuit = _upsert_circuit(
                db=db,
                cache=circuit_cache,
                race=result_race,
                observed_laps=_max_laps(entries),
                first_gp_year_by_circuit=first_gp_year_by_circuit,
                client=client,
                issues=result.data_issues,
            )

            race = _upsert_race(db, result_race, circuit.circuit_id, entries)
            result.races_loaded += 1

            seen_driver_ids: set[str] = set()
            for entry in entries:
                driver = _upsert_driver(db, driver_cache, entry["Driver"])
                constructor = _upsert_constructor(db, constructor_cache, entry["Constructor"])
                seen_driver_ids.add(driver.driver_id)
                driver_stats[driver.driver_id]
                constructor_stats[constructor.constructor_id]
                classified_status = _classify_result_status(entry)
                finish_position = (
                    _to_int(entry.get("position")) if classified_status == DriverResultStatus.FINISHED.value else None
                )
                points = _to_float(entry.get("points"), default=0.0)

                _upsert_race_entry(
                    db=db,
                    race_id=race.race_id,
                    driver_id=driver.driver_id,
                    constructor_id=constructor.constructor_id,
                    grid_position=_to_int(entry.get("grid")),
                    finish_position=finish_position,
                    status=classified_status,
                    points=points,
                )
                result.race_entries_loaded += 1

                if finish_position == 1:
                    driver_stats[driver.driver_id]["wins"] += 1
                    constructor_stats[constructor.constructor_id]["wins"] += 1
                if finish_position is not None and finish_position <= 3:
                    driver_stats[driver.driver_id]["podiums"] += 1
                    constructor_stats[constructor.constructor_id]["podiums"] += 1

                driver_points_by_season[season][driver.driver_id] += points
                constructor_points_by_season[season][constructor.constructor_id] += points
                latest_constructor_by_driver[driver.driver_id] = (
                    season,
                    round_number,
                    constructor.constructor_id,
                )

                _maybe_track_fastest_lap(
                    fastest_lap_by_circuit,
                    circuit.circuit_id,
                    entry,
                    driver.driver_id,
                    season,
                )

            if seen_driver_ids:
                (
                    db.query(RaceEntry)
                    .filter(
                        RaceEntry.race_id == race.race_id,
                        RaceEntry.driver_id.notin_(seen_driver_ids),
                    )
                    .delete(synchronize_session=False)
                )

            # Flush per race, not just once per season: db.get() in
            # _upsert_driver/_upsert_constructor/_upsert_circuit only sees
            # PERSISTENT rows, not objects added-but-unflushed earlier in the
            # same run. Without this, a constructor seen in race 1 isn't
            # recognized as existing when race 2 of the same season upserts
            # it again, producing duplicate INSERTs and a UNIQUE violation.
            db.flush()

            pole = poles_by_round.get(round_number)
            if pole is not None:
                pole_driver_id, pole_constructor_id = pole
                driver_stats[pole_driver_id]["poles"] += 1
                constructor_stats[pole_constructor_id]["poles"] += 1

        db.flush()

    _apply_championship_counts(driver_stats, driver_points_by_season)
    _apply_championship_counts(constructor_stats, constructor_points_by_season)
    _apply_partial_career_stats(db, driver_stats, constructor_stats, latest_constructor_by_driver)
    _apply_lap_records(db, fastest_lap_by_circuit)
    db.commit()
    return result


def _fetch_poles_by_round(
    client: JolpicaClient, season: int, load_result: JolpicaLoadResult
) -> dict[int, tuple[str, str]]:
    poles: dict[int, tuple[str, str]] = {}
    try:
        qualifying_races = client.race_table(f"{season}/qualifying")
    except requests.HTTPError as exc:
        load_result.data_issues.append(f"{season}: qualifying data unavailable ({exc})")
        return poles

    for race in qualifying_races:
        qualifying_results = race.get("QualifyingResults", [])
        for row in qualifying_results:
            if _to_int(row.get("position")) == 1:
                poles[int(race["round"])] = (
                    row["Driver"]["driverId"],
                    row["Constructor"]["constructorId"],
                )
                break

    return poles


def _upsert_circuit(
    db: Session,
    cache: dict[str, Circuit],
    race: dict[str, Any],
    observed_laps: int | None,
    first_gp_year_by_circuit: dict[str, int],
    client: JolpicaClient,
    issues: list[str],
) -> Circuit:
    source = race["Circuit"]
    circuit_id = source["circuitId"]
    location = source.get("Location", {})

    length_km = CIRCUIT_LENGTH_KM.get(circuit_id)
    if length_km is None:
        length_km = 0.0
        if f"{circuit_id}: missing circuit length" not in issues:
            issues.append(f"{circuit_id}: missing circuit length from Jolpica and local length map")

    circuit = cache.get(circuit_id) or db.get(Circuit, circuit_id)

    # first_gp_year never changes for a circuit once known -- reuse an
    # already-persisted value (from this run's cache or a prior ETL run)
    # instead of re-fetching it. Without this, every rerun of an already-
    # ingested season burns one extra API call per circuit for nothing,
    # which is exactly what tipped a same-day rerun into a 429.
    first_gp_year = first_gp_year_by_circuit.get(circuit_id)
    if first_gp_year is None and circuit is not None:
        first_gp_year = circuit.first_gp_year
    if first_gp_year is None:
        first_gp_year = _fetch_first_gp_year(client, circuit_id, int(race["season"]), issues)
    first_gp_year_by_circuit[circuit_id] = first_gp_year

    if circuit is None:
        circuit = Circuit(
            circuit_id=circuit_id,
            name=source["circuitName"],
            country=location.get("country") or "",
            locality=location.get("locality") or "",
            length_km=length_km,
            laps=observed_laps or 0,
            first_gp_year=first_gp_year,
            lap_record_time=None,
            lap_record_driver_id=None,
            lap_record_year=None,
            downforce_level=None,
            key_trait=None,
            trivia=[],
        )
        db.add(circuit)
    else:
        circuit.name = source["circuitName"]
        circuit.country = location.get("country") or circuit.country
        circuit.locality = location.get("locality") or circuit.locality
        circuit.length_km = length_km
        if observed_laps is not None:
            circuit.laps = observed_laps
        circuit.first_gp_year = min(circuit.first_gp_year, first_gp_year)
        # downforce_level, key_trait, and trivia are curated editorial fields.
        # ETL intentionally leaves existing values untouched on reruns.

    cache[circuit_id] = circuit
    return circuit


def _upsert_race(
    db: Session, race_source: dict[str, Any], circuit_id: str, entries: list[dict[str, Any]]
) -> Race:
    race_id = _race_id(race_source)
    race = db.get(Race, race_id)
    race_date = date.fromisoformat(race_source["date"])
    total_laps = _max_laps(entries)
    status = RaceStatus.COMPLETED.value if entries else RaceStatus.UPCOMING.value

    if race is None:
        race = Race(
            race_id=race_id,
            season=int(race_source["season"]),
            round=int(race_source["round"]),
            name=race_source["raceName"],
            circuit_id=circuit_id,
            date=race_date,
            status=status,
            total_laps=total_laps,
        )
        db.add(race)
    else:
        race.season = int(race_source["season"])
        race.round = int(race_source["round"])
        race.name = race_source["raceName"]
        race.circuit_id = circuit_id
        race.date = race_date
        race.status = status
        race.total_laps = total_laps or race.total_laps

    return race


def _upsert_driver(db: Session, cache: dict[str, Driver], source: dict[str, Any]) -> Driver:
    driver_id = source["driverId"]
    driver = cache.get(driver_id) or db.get(Driver, driver_id)
    if driver is None:
        driver = Driver(
            driver_id=driver_id,
            name=f"{source.get('givenName', '').strip()} {source.get('familyName', '').strip()}".strip(),
            nationality=source.get("nationality") or "",
            date_of_birth=date.fromisoformat(source["dateOfBirth"]),
            current_constructor_id=None,
            career_wins=0,
            career_podiums=0,
            career_poles=0,
            career_championships=0,
        )
        db.add(driver)
    else:
        driver.name = f"{source.get('givenName', '').strip()} {source.get('familyName', '').strip()}".strip()
        driver.nationality = source.get("nationality") or driver.nationality
        if source.get("dateOfBirth"):
            driver.date_of_birth = date.fromisoformat(source["dateOfBirth"])
    cache[driver_id] = driver
    return driver


def _upsert_constructor(db: Session, cache: dict[str, Constructor], source: dict[str, Any]) -> Constructor:
    constructor_id = source["constructorId"]
    constructor = cache.get(constructor_id) or db.get(Constructor, constructor_id)
    if constructor is None:
        constructor = Constructor(
            constructor_id=constructor_id,
            name=source["name"],
            nationality=source.get("nationality") or "",
            career_wins=0,
            career_podiums=0,
            career_poles=0,
            career_championships=0,
        )
        db.add(constructor)
    else:
        constructor.name = source["name"]
        constructor.nationality = source.get("nationality") or constructor.nationality
    cache[constructor_id] = constructor
    return constructor


def _upsert_race_entry(
    db: Session,
    race_id: str,
    driver_id: str,
    constructor_id: str,
    grid_position: int | None,
    finish_position: int | None,
    status: str,
    points: float,
) -> RaceEntry:
    entry = (
        db.query(RaceEntry)
        .filter(RaceEntry.race_id == race_id, RaceEntry.driver_id == driver_id)
        .one_or_none()
    )
    if entry is None:
        entry = RaceEntry(race_id=race_id, driver_id=driver_id, constructor_id=constructor_id)
        db.add(entry)

    entry.constructor_id = constructor_id
    entry.grid_position = grid_position
    entry.finish_position = finish_position
    entry.status = status
    entry.points = points
    return entry


def _fetch_first_gp_year(
    client: JolpicaClient, circuit_id: str, fallback_year: int, issues: list[str]
) -> int:
    try:
        races = client.race_table(f"circuits/{circuit_id}/races")
    except requests.HTTPError as exc:
        issues.append(f"{circuit_id}: could not fetch first GP year ({exc})")
        return fallback_year

    if not races:
        issues.append(f"{circuit_id}: Jolpica returned no historical races for first GP year")
        return fallback_year
    return int(races[0]["season"])


def _apply_championship_counts(
    stats: dict[str, dict[str, int]], points_by_season: dict[int, dict[str, float]]
) -> None:
    for season_points in points_by_season.values():
        if not season_points:
            continue
        champion_id = max(season_points.items(), key=lambda item: item[1])[0]
        stats[champion_id]["championships"] += 1


def _apply_partial_career_stats(
    db: Session,
    driver_stats: dict[str, dict[str, int]],
    constructor_stats: dict[str, dict[str, int]],
    latest_constructor_by_driver: dict[str, tuple[int, int, str]],
) -> None:
    # These are computed only from the season range ingested in this ETL run.
    # They are not full career totals unless the caller ingests the full F1
    # history back to 1950 in one run.
    for driver_id, stats in driver_stats.items():
        driver = db.get(Driver, driver_id)
        if driver is None:
            continue
        driver.career_wins = stats["wins"]
        driver.career_podiums = stats["podiums"]
        driver.career_poles = stats["poles"]
        driver.career_championships = stats["championships"]

    for constructor_id, stats in constructor_stats.items():
        constructor = db.get(Constructor, constructor_id)
        if constructor is None:
            continue
        constructor.career_wins = stats["wins"]
        constructor.career_podiums = stats["podiums"]
        constructor.career_poles = stats["poles"]
        constructor.career_championships = stats["championships"]

    for driver_id, (_, _, constructor_id) in latest_constructor_by_driver.items():
        driver = db.get(Driver, driver_id)
        if driver is not None:
            driver.current_constructor_id = constructor_id


def _apply_lap_records(
    db: Session, fastest_lap_by_circuit: dict[str, tuple[float, str, str, int]]
) -> None:
    # Compare against whatever's already stored, not just this run's range --
    # otherwise a later run covering only newer/slower seasons (e.g. ingesting
    # 2018-2020 first, then 2024 separately) would overwrite a genuinely
    # faster record from a season this run didn't touch.
    for circuit_id, (seconds, lap_time, driver_id, year) in fastest_lap_by_circuit.items():
        circuit = db.get(Circuit, circuit_id)
        if circuit is None:
            continue
        existing_seconds = (
            _lap_time_to_seconds(circuit.lap_record_time) if circuit.lap_record_time else None
        )
        if existing_seconds is not None and existing_seconds <= seconds:
            continue
        circuit.lap_record_time = lap_time
        circuit.lap_record_driver_id = driver_id
        circuit.lap_record_year = year


def _maybe_track_fastest_lap(
    fastest_lap_by_circuit: dict[str, tuple[float, str, str, int]],
    circuit_id: str,
    entry: dict[str, Any],
    driver_id: str,
    season: int,
) -> None:
    fastest = entry.get("FastestLap") or {}
    lap_time = (fastest.get("Time") or {}).get("time")
    if not lap_time:
        return
    seconds = _lap_time_to_seconds(lap_time)
    current = fastest_lap_by_circuit.get(circuit_id)
    if current is None or seconds < current[0]:
        fastest_lap_by_circuit[circuit_id] = (seconds, lap_time, driver_id, season)


def _race_id(race: dict[str, Any]) -> str:
    return f"{int(race['season'])}-{race['Circuit']['circuitId']}"


def _max_laps(entries: list[dict[str, Any]]) -> int | None:
    laps = [_to_int(entry.get("laps")) for entry in entries]
    numeric_laps = [lap for lap in laps if lap is not None]
    return max(numeric_laps) if numeric_laps else None


def _classify_result_status(entry: dict[str, Any]) -> str:
    status = (entry.get("status") or "").strip().lower()
    position_text = (entry.get("positionText") or "").strip().lower()

    if status == "finished" or status.startswith("+"):
        return DriverResultStatus.FINISHED.value
    if "disqualified" in status or position_text == "d":
        return DriverResultStatus.DSQ.value
    if "did not start" in status or "withdraw" in status or position_text == "w":
        return DriverResultStatus.DNS.value
    return DriverResultStatus.DNF.value


def _lap_time_to_seconds(value: str) -> float:
    minutes, seconds = value.split(":", 1)
    return int(minutes) * 60 + float(seconds)


def _to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
