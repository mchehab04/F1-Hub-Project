from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.tables import Constructor, Driver, Race, RaceEntry
from app.schemas.constructors import (
    ConstructorCareer,
    ConstructorCompareResponse,
    ConstructorHeadToHead,
    ConstructorProfileResponse,
)

router = APIRouter(tags=["constructors"])


# NOTE: /compare must be registered before /{constructor_id} so FastAPI
# doesn't match "compare" as a constructor_id path parameter.
@router.get("/constructors/compare", response_model=ConstructorCompareResponse)
def compare_constructors(
    constructor_a: str,
    constructor_b: str,
    season: int | None = None,
    db: Session = Depends(get_db),
):
    _ensure_constructor_competed(constructor_a, season, db)
    _ensure_constructor_competed(constructor_b, season, db)

    race_wins = {constructor_a: 0, constructor_b: 0}
    points = {constructor_a: 0.0, constructor_b: 0.0}
    podiums = {constructor_a: 0, constructor_b: 0}

    for constructor_id in (constructor_a, constructor_b):
        rows = _constructor_entries(constructor_id, season, db)
        for row in rows:
            points[constructor_id] += row.points or 0.0
            if row.finish_position == 1:
                race_wins[constructor_id] += 1
            if row.finish_position in (1, 2, 3):
                podiums[constructor_id] += 1

    return ConstructorCompareResponse(
        constructor_a=constructor_a,
        constructor_b=constructor_b,
        season=season,
        head_to_head=ConstructorHeadToHead(
            race_wins=race_wins,
            points=points,
            podiums=podiums,
        ),
    )


@router.get("/constructors/{constructor_id}", response_model=ConstructorProfileResponse)
def get_constructor(constructor_id: str, db: Session = Depends(get_db)):
    constructor = db.get(Constructor, constructor_id)
    if constructor is None:
        raise HTTPException(status_code=404, detail=f"constructor {constructor_id} not found")

    current_drivers = db.execute(
        select(Driver.driver_id)
        .where(Driver.current_constructor_id == constructor_id)
        .order_by(Driver.driver_id)
    ).scalars().all()

    return ConstructorProfileResponse(
        constructor_id=constructor.constructor_id,
        name=constructor.name,
        nationality=constructor.nationality,
        current_drivers=current_drivers,
        career=ConstructorCareer(
            wins=constructor.career_wins,
            podiums=constructor.career_podiums,
            poles=constructor.career_poles,
            championships=constructor.career_championships,
        ),
    )


def _ensure_constructor_competed(constructor_id: str, season: int | None, db: Session):
    query = (
        select(func.count())
        .select_from(RaceEntry)
        .where(RaceEntry.constructor_id == constructor_id)
    )
    if season is not None:
        query = query.join(Race, RaceEntry.race_id == Race.race_id).where(Race.season == season)

    if db.execute(query).scalar_one() == 0:
        detail = (
            f"constructor {constructor_id} did not compete in season {season}"
            if season is not None
            else f"constructor {constructor_id} did not compete"
        )
        raise HTTPException(status_code=404, detail=detail)


def _constructor_entries(constructor_id: str, season: int | None, db: Session):
    query = select(RaceEntry.finish_position, RaceEntry.points).where(
        RaceEntry.constructor_id == constructor_id
    )
    if season is not None:
        query = query.join(Race, RaceEntry.race_id == Race.race_id).where(Race.season == season)

    return db.execute(query).all()
