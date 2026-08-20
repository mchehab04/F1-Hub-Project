"""ETL orchestration entrypoint.

Run from the backend directory, for example:
python -m etl.build_db --seasons 2024
python -m etl.build_db --start-season 2024 --end-season 2024
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.db.tables import (
    Base,
    Circuit,
    Constructor,
    Driver,
    ModelVersion,
    Prediction,
    Race,
    RaceEntry,
    ReplayLap,
    SessionWeather,
)
from etl.fetch_fastf1 import load_fastf1_data
from etl.fetch_jolpica import load_jolpica_data


@dataclass(frozen=True)
class SeasonRange:
    start: int
    end: int


def main() -> None:
    args = _parse_args()
    season_range = _resolve_season_range(args)
    build_database(season_range.start, season_range.end)


def build_database(start_season: int, end_season: int) -> None:
    if start_season > end_season:
        raise ValueError("start season must be <= end season")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        jolpica_result = load_jolpica_data(db, start_season, end_season)
        fastf1_result = load_fastf1_data(db, start_season, end_season)
        counts = _table_counts(db)
    finally:
        db.close()

    print(f"Loaded seasons {start_season}-{end_season}")
    print(
        "Jolpica: "
        f"{jolpica_result.races_loaded} races, "
        f"{jolpica_result.race_entries_loaded} race entries"
    )
    print(
        "FastF1: "
        f"{fastf1_result.races_attempted} races attempted, "
        f"{fastf1_result.weather_rows_loaded} weather rows, "
        f"{fastf1_result.replay_laps_loaded} replay laps"
    )
    print("Table counts:")
    for table_name, count in counts.items():
        print(f"  {table_name}: {count}")

    issues = jolpica_result.data_issues + fastf1_result.data_issues
    if issues:
        print("Data issues:")
        for issue in issues:
            print(f"  - {issue}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Populate the F1Hub SQLite database")
    parser.add_argument(
        "--seasons",
        help="Single season or inclusive range, e.g. 2024 or 2021-2024",
    )
    parser.add_argument("--start-season", type=int)
    parser.add_argument("--end-season", type=int)
    return parser.parse_args()


def _resolve_season_range(args: argparse.Namespace) -> SeasonRange:
    if args.seasons:
        if args.start_season is not None or args.end_season is not None:
            raise ValueError("use either --seasons or --start-season/--end-season, not both")
        return _parse_seasons_arg(args.seasons)

    if args.start_season is None and args.end_season is None:
        raise ValueError("provide --seasons or --start-season/--end-season")
    if args.start_season is None or args.end_season is None:
        season = args.start_season or args.end_season
        return SeasonRange(season, season)
    return SeasonRange(args.start_season, args.end_season)


def _parse_seasons_arg(value: str) -> SeasonRange:
    if "-" in value:
        start, end = value.split("-", 1)
        return SeasonRange(int(start), int(end))
    season = int(value)
    return SeasonRange(season, season)


def _table_counts(db: Session) -> dict[str, int]:
    tables = [
        Circuit,
        Driver,
        Constructor,
        Race,
        RaceEntry,
        SessionWeather,
        ReplayLap,
        ModelVersion,
        Prediction,
    ]
    return {
        table.__tablename__: db.scalar(select(func.count()).select_from(table)) or 0
        for table in tables
    }


if __name__ == "__main__":
    main()
