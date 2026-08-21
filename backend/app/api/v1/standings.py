from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.tables import Constructor, Race, RaceEntry, RaceStatus
from app.schemas.standings import (
    ConstructorStanding,
    ConstructorStandingsResponse,
    DriverStanding,
    DriverStandingsResponse,
)

router = APIRouter(tags=["standings"])


@router.get("/standings/drivers", response_model=DriverStandingsResponse)
def get_driver_standings(season: int, db: Session = Depends(get_db)):
    rows = _completed_race_entries(season, db)
    if not rows:
        # No completed races is not exceptional for future/in-progress seasons.
        return DriverStandingsResponse(season=season, as_of_round=0, standings=[])

    as_of_round = max(row.round for row in rows)
    standings_by_driver = {}

    for row in rows:
        standing = standings_by_driver.setdefault(
            row.driver_id,
            {
                "driver_id": row.driver_id,
                "constructor_id": row.constructor_id,
                "constructor_name": row.constructor_name,
                "latest_round": row.round,
                "points": 0.0,
                "wins": 0,
                "podiums": 0,
                "trend": [0.0] * as_of_round,
            },
        )

        points = row.points or 0.0
        standing["points"] += points
        standing["trend"][row.round - 1] += points
        if row.finish_position == 1:
            standing["wins"] += 1
        if row.finish_position in (1, 2, 3):
            standing["podiums"] += 1

        if row.round >= standing["latest_round"]:
            standing["latest_round"] = row.round
            standing["constructor_id"] = row.constructor_id
            standing["constructor_name"] = row.constructor_name

    # The contract does not define tied-points behavior; use wins, then driver_id
    # for a deterministic ordinal ranking.
    ranked = sorted(
        standings_by_driver.values(),
        key=lambda standing: (-standing["points"], -standing["wins"], standing["driver_id"]),
    )

    standings = [
        DriverStanding(
            driver_id=standing["driver_id"],
            constructor_id=standing["constructor_id"],
            constructor_name=standing["constructor_name"],
            position=position,
            points=standing["points"],
            wins=standing["wins"],
            podiums=standing["podiums"],
            trend=standing["trend"],
        )
        for position, standing in enumerate(ranked, start=1)
    ]
    return DriverStandingsResponse(season=season, as_of_round=as_of_round, standings=standings)


@router.get("/standings/constructors", response_model=ConstructorStandingsResponse)
def get_constructor_standings(season: int, db: Session = Depends(get_db)):
    rows = _completed_race_entries(season, db)
    if not rows:
        # No completed races is not exceptional for future/in-progress seasons.
        return ConstructorStandingsResponse(season=season, as_of_round=0, standings=[])

    as_of_round = max(row.round for row in rows)
    standings_by_constructor = {}

    for row in rows:
        standing = standings_by_constructor.setdefault(
            row.constructor_id,
            {
                "constructor_id": row.constructor_id,
                "points": 0.0,
                "wins": 0,
                "podiums": 0,
                "trend": [0.0] * as_of_round,
            },
        )

        points = row.points or 0.0
        standing["points"] += points
        standing["trend"][row.round - 1] += points
        if row.finish_position == 1:
            standing["wins"] += 1
        if row.finish_position in (1, 2, 3):
            standing["podiums"] += 1

    # The contract does not define tied-points behavior; use wins, then
    # constructor_id for a deterministic ordinal ranking.
    ranked = sorted(
        standings_by_constructor.values(),
        key=lambda standing: (
            -standing["points"],
            -standing["wins"],
            standing["constructor_id"],
        ),
    )

    standings = [
        ConstructorStanding(
            constructor_id=standing["constructor_id"],
            position=position,
            points=standing["points"],
            wins=standing["wins"],
            podiums=standing["podiums"],
            trend=standing["trend"],
        )
        for position, standing in enumerate(ranked, start=1)
    ]
    return ConstructorStandingsResponse(season=season, as_of_round=as_of_round, standings=standings)


def _completed_race_entries(season: int, db: Session):
    return db.execute(
        select(
            Race.round.label("round"),
            RaceEntry.driver_id.label("driver_id"),
            RaceEntry.constructor_id.label("constructor_id"),
            Constructor.name.label("constructor_name"),
            RaceEntry.finish_position.label("finish_position"),
            RaceEntry.points.label("points"),
        )
        .join(Race, RaceEntry.race_id == Race.race_id)
        .join(Constructor, RaceEntry.constructor_id == Constructor.constructor_id)
        .where(Race.season == season, Race.status == RaceStatus.COMPLETED.value)
        .order_by(Race.round, RaceEntry.driver_id)
    ).all()
