from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.db.session import get_db
from app.db.tables import Driver, Race, RaceEntry
from app.schemas.drivers import (
    DriverCareer,
    DriverCompareResponse,
    DriverHeadToHead,
    DriverProfileResponse,
)

router = APIRouter(tags=["drivers"])


# NOTE: /compare must be registered before /{driver_id} so FastAPI doesn't
# match "compare" as a driver_id path parameter.
@router.get("/drivers/compare", response_model=DriverCompareResponse)
def compare_drivers(
    driver_a: str,
    driver_b: str,
    season: int | None = None,
    db: Session = Depends(get_db),
):
    _ensure_driver_raced(driver_a, season, db)
    _ensure_driver_raced(driver_b, season, db)

    entry_a = aliased(RaceEntry)
    entry_b = aliased(RaceEntry)

    query = (
        select(
            entry_a.points.label("points_a"),
            entry_b.points.label("points_b"),
            entry_a.finish_position.label("finish_position_a"),
            entry_b.finish_position.label("finish_position_b"),
            entry_a.grid_position.label("grid_position_a"),
            entry_b.grid_position.label("grid_position_b"),
        )
        .join(entry_b, entry_a.race_id == entry_b.race_id)
        .join(Race, entry_a.race_id == Race.race_id)
        .where(entry_a.driver_id == driver_a, entry_b.driver_id == driver_b)
    )
    if season is not None:
        query = query.where(Race.season == season)

    points = {driver_a: 0.0, driver_b: 0.0}
    qualifying_wins = {driver_a: 0, driver_b: 0}
    race_finish_wins = {driver_a: 0, driver_b: 0}

    for row in db.execute(query).all():
        points[driver_a] += row.points_a or 0.0
        points[driver_b] += row.points_b or 0.0
        _count_position_win(
            row.grid_position_a,
            row.grid_position_b,
            driver_a,
            driver_b,
            qualifying_wins,
        )
        _count_position_win(
            row.finish_position_a,
            row.finish_position_b,
            driver_a,
            driver_b,
            race_finish_wins,
        )

    return DriverCompareResponse(
        driver_a=driver_a,
        driver_b=driver_b,
        season=season,
        head_to_head=DriverHeadToHead(
            qualifying_wins=qualifying_wins,
            race_finish_wins=race_finish_wins,
            points=points,
        ),
    )


@router.get("/drivers/{driver_id}", response_model=DriverProfileResponse)
def get_driver(driver_id: str, db: Session = Depends(get_db)):
    driver = db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail=f"driver {driver_id} not found")

    return DriverProfileResponse(
        driver_id=driver.driver_id,
        name=driver.name,
        nationality=driver.nationality,
        date_of_birth=driver.date_of_birth,
        current_constructor_id=driver.current_constructor_id,
        career=DriverCareer(
            wins=driver.career_wins,
            podiums=driver.career_podiums,
            poles=driver.career_poles,
            championships=driver.career_championships,
        ),
    )


def _ensure_driver_raced(driver_id: str, season: int | None, db: Session):
    query = select(func.count()).select_from(RaceEntry).where(RaceEntry.driver_id == driver_id)
    if season is not None:
        query = query.join(Race, RaceEntry.race_id == Race.race_id).where(Race.season == season)

    if db.execute(query).scalar_one() == 0:
        detail = (
            f"driver {driver_id} did not race in season {season}"
            if season is not None
            else f"driver {driver_id} did not race"
        )
        raise HTTPException(status_code=404, detail=detail)


def _count_position_win(
    position_a: int | None,
    position_b: int | None,
    driver_a: str,
    driver_b: str,
    totals: dict[str, int],
):
    if position_a is not None and (position_b is None or position_a < position_b):
        totals[driver_a] += 1
    elif position_b is not None and (position_a is None or position_b < position_a):
        totals[driver_b] += 1
