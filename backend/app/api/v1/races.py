from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.tables import Constructor, Race, RaceEntry, RaceStatus
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


@router.get("/races/{race_id}/replay")
def get_replay(race_id: str):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")
