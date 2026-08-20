from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.tables import Circuit, Race
from app.schemas.seasons import SeasonRace, SeasonRacesResponse, SeasonsResponse

router = APIRouter(tags=["seasons"])


@router.get("/seasons", response_model=SeasonsResponse)
def list_seasons(db: Session = Depends(get_db)):
    seasons = db.scalars(select(Race.season).distinct().order_by(Race.season)).all()
    return SeasonsResponse(seasons=list(seasons))


@router.get("/seasons/{season}/races", response_model=SeasonRacesResponse)
def list_races(season: int, db: Session = Depends(get_db)):
    rows = db.execute(
        select(Race, Circuit.name)
        .join(Circuit, Race.circuit_id == Circuit.circuit_id)
        .where(Race.season == season)
        .order_by(Race.round)
    ).all()

    races = [
        SeasonRace(
            race_id=race.race_id,
            round=race.round,
            name=race.name,
            circuit_id=race.circuit_id,
            circuit_name=circuit_name,
            date=race.date,
            status=race.status,
        )
        for race, circuit_name in rows
    ]
    return SeasonRacesResponse(season=season, races=races)


@router.get("/seasons/{season}/accuracy")
def get_season_accuracy(season: int):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")
