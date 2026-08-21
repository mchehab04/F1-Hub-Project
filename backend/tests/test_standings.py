from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.db.tables import Base, Constructor, Driver, Race, RaceEntry, RaceStatus
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        db.add_all(
            [
                Constructor(
                    constructor_id="red_bull",
                    name="Red Bull Racing",
                    nationality="Austrian",
                ),
                Constructor(
                    constructor_id="mclaren",
                    name="McLaren",
                    nationality="British",
                ),
                Constructor(
                    constructor_id="ferrari",
                    name="Ferrari",
                    nationality="Italian",
                ),
                Driver(
                    driver_id="verstappen",
                    name="Max Verstappen",
                    nationality="Dutch",
                    date_of_birth=date(1997, 9, 30),
                ),
                Driver(
                    driver_id="norris",
                    name="Lando Norris",
                    nationality="British",
                    date_of_birth=date(1999, 11, 13),
                ),
                Driver(
                    driver_id="sainz",
                    name="Carlos Sainz",
                    nationality="Spanish",
                    date_of_birth=date(1994, 9, 1),
                ),
                Race(
                    race_id="2026-bahrain",
                    season=2026,
                    round=1,
                    name="Bahrain Grand Prix",
                    circuit_id="bahrain",
                    date=date(2026, 3, 8),
                    status=RaceStatus.COMPLETED.value,
                ),
                Race(
                    race_id="2026-jeddah",
                    season=2026,
                    round=2,
                    name="Saudi Arabian Grand Prix",
                    circuit_id="jeddah",
                    date=date(2026, 3, 15),
                    status=RaceStatus.COMPLETED.value,
                ),
                Race(
                    race_id="2026-melbourne",
                    season=2026,
                    round=3,
                    name="Australian Grand Prix",
                    circuit_id="albert_park",
                    date=date(2026, 3, 29),
                    status=RaceStatus.UPCOMING.value,
                ),
            ]
        )
        db.flush()
        db.add_all(
            [
                RaceEntry(
                    race_id="2026-bahrain",
                    driver_id="verstappen",
                    constructor_id="red_bull",
                    finish_position=1,
                    status="finished",
                    points=25,
                ),
                RaceEntry(
                    race_id="2026-bahrain",
                    driver_id="norris",
                    constructor_id="mclaren",
                    finish_position=2,
                    status="finished",
                    points=18,
                ),
                RaceEntry(
                    race_id="2026-bahrain",
                    driver_id="sainz",
                    constructor_id="ferrari",
                    finish_position=3,
                    status="finished",
                    points=15,
                ),
                RaceEntry(
                    race_id="2026-jeddah",
                    driver_id="verstappen",
                    constructor_id="red_bull",
                    finish_position=2,
                    status="finished",
                    points=18,
                ),
                RaceEntry(
                    race_id="2026-jeddah",
                    driver_id="norris",
                    constructor_id="mclaren",
                    finish_position=1,
                    status="finished",
                    points=25,
                ),
                RaceEntry(
                    race_id="2026-jeddah",
                    driver_id="sainz",
                    constructor_id="mclaren",
                    finish_position=4,
                    status="finished",
                    points=12,
                ),
            ]
        )
        db.commit()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_driver_standings_aggregate_completed_races_and_latest_constructor(client):
    response = client.get("/api/v1/standings/drivers?season=2026")

    assert response.status_code == 200
    body = response.json()
    assert body["season"] == 2026
    assert body["as_of_round"] == 2

    assert body["standings"][0] == {
        "driver_id": "norris",
        "constructor_id": "mclaren",
        "constructor_name": "McLaren",
        "position": 1,
        "points": 43.0,
        "wins": 1,
        "podiums": 2,
        "trend": [18.0, 25.0],
    }

    sainz = next(standing for standing in body["standings"] if standing["driver_id"] == "sainz")
    assert sainz["constructor_id"] == "mclaren"
    assert sainz["constructor_name"] == "McLaren"
    assert sainz["points"] == 27.0
    assert sainz["podiums"] == 1
    assert sainz["trend"] == [15.0, 12.0]


def test_constructor_standings_combine_drivers(client):
    response = client.get("/api/v1/standings/constructors?season=2026")

    assert response.status_code == 200
    body = response.json()
    assert body["as_of_round"] == 2
    assert body["standings"][0] == {
        "constructor_id": "mclaren",
        "position": 1,
        "points": 55.0,
        "wins": 1,
        "podiums": 2,
        "trend": [18.0, 37.0],
    }


def test_standings_empty_when_season_has_no_completed_races(client):
    response = client.get("/api/v1/standings/drivers?season=2027")

    assert response.status_code == 200
    assert response.json() == {"season": 2027, "as_of_round": 0, "standings": []}
