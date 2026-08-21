from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.tables import Constructor, Race, RaceEntry, RaceStatus, ReplayLap
from app.schemas.replay import ReplayDriver, ReplayLap as ReplayLapSchema, ReplayResponse
from app.schemas.races import RaceResponse, RaceResult

router = APIRouter(tags=["races"])


@router.get("/races/{race_id}", response_model=RaceResponse)
def get_race(race_id: str, db: Session = Depends(get_db)):
    race = db.get(Race, race_id)
    if race is None:
        raise HTTPException(status_code=404, detail="race not found")

    results = None
    if race.status == RaceStatus.COMPLETED.value:
        rows = db.execute(
            select(RaceEntry, Constructor.name)
            .join(Constructor, RaceEntry.constructor_id == Constructor.constructor_id)
            .where(RaceEntry.race_id == race_id)
            .order_by(
                case((RaceEntry.finish_position.is_(None), 1), else_=0),
                RaceEntry.finish_position,
                RaceEntry.grid_position,
                RaceEntry.driver_id,
            )
        ).all()
        results = [
            RaceResult(
                driver_id=entry.driver_id,
                constructor_id=entry.constructor_id,
                constructor_name=constructor_name,
                grid_position=entry.grid_position,
                finish_position=entry.finish_position,
                status=entry.status,
                points=entry.points,
            )
            for entry, constructor_name in rows
        ]

    return RaceResponse(
        race_id=race.race_id,
        round=race.round,
        season=race.season,
        name=race.name,
        circuit_id=race.circuit_id,
        date=race.date,
        status=race.status,
        results=results,
    )


@router.get("/races/{race_id}/prediction")
def get_prediction(race_id: str):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")


@router.get("/races/{race_id}/accuracy")
def get_race_accuracy(race_id: str):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")


@router.get("/races/{race_id}/replay", response_model=ReplayResponse)
def get_replay(race_id: str, db: Session = Depends(get_db)):
    race = db.get(Race, race_id)
    if race is None:
        raise HTTPException(status_code=404, detail="race not found")

    if race.season < 2018:
        raise HTTPException(
            status_code=404,
            detail="no replay data available for races before 2018 (FastF1 coverage begins in 2018)",
        )

    if race.status != RaceStatus.COMPLETED.value:
        raise HTTPException(
            status_code=409,
            detail=f"race {race_id} has not been completed yet",
        )

    rows = db.execute(
        select(ReplayLap)
        .where(ReplayLap.race_id == race_id)
        .order_by(ReplayLap.driver_id, ReplayLap.lap)
    ).scalars()

    drivers_by_id: dict[str, ReplayDriver] = {}
    for row in rows:
        driver = drivers_by_id.setdefault(
            row.driver_id,
            ReplayDriver(driver_id=row.driver_id, laps=[]),
        )
        driver.laps.append(
            ReplayLapSchema(
                lap=row.lap,
                position=row.position,
                gap_to_leader_s=row.gap_to_leader_s,
            )
        )

    if not drivers_by_id:
        raise HTTPException(
            status_code=404,
            detail=f"replay data not found for race {race_id}",
        )

    return ReplayResponse(
        race_id=race.race_id,
        total_laps=race.total_laps,
        drivers=list(drivers_by_id.values()),
    )
