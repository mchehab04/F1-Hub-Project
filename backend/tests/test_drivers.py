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
                    current_constructor_id="red_bull",
                    career_wins=63,
                    career_podiums=112,
                    career_poles=40,
                    career_championships=4,
                ),
                Driver(
                    driver_id="norris",
                    name="Lando Norris",
                    nationality="British",
                    date_of_birth=date(1999, 11, 13),
                    current_constructor_id="mclaren",
                    career_wins=9,
                    career_podiums=42,
                    career_poles=12,
                    career_championships=0,
                ),
                Driver(
                    driver_id="alonso",
                    name="Fernando Alonso",
                    nationality="Spanish",
                    date_of_birth=date(1981, 7, 29),
                    current_constructor_id="ferrari",
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
                    race_id="2025-monza",
                    season=2025,
                    round=16,
                    name="Italian Grand Prix",
                    circuit_id="monza",
                    date=date(2025, 9, 7),
                    status=RaceStatus.COMPLETED.value,
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
                    grid_position=1,
                    finish_position=1,
                    status="finished",
                    points=25,
                ),
                RaceEntry(
                    race_id="2026-bahrain",
                    driver_id="norris",
                    constructor_id="mclaren",
                    grid_position=2,
                    finish_position=2,
                    status="finished",
                    points=18,
                ),
                RaceEntry(
                    race_id="2026-jeddah",
                    driver_id="verstappen",
                    constructor_id="red_bull",
                    grid_position=3,
                    finish_position=None,
                    status="dnf",
                    points=0,
                ),
                RaceEntry(
                    race_id="2026-jeddah",
                    driver_id="norris",
                    constructor_id="mclaren",
                    grid_position=1,
                    finish_position=1,
                    status="finished",
                    points=25,
                ),
                RaceEntry(
                    race_id="2025-monza",
                    driver_id="verstappen",
                    constructor_id="red_bull",
                    grid_position=2,
                    finish_position=2,
                    status="finished",
                    points=18,
                ),
                RaceEntry(
                    race_id="2025-monza",
                    driver_id="norris",
                    constructor_id="mclaren",
                    grid_position=1,
                    finish_position=1,
                    status="finished",
                    points=25,
                ),
                RaceEntry(
                    race_id="2025-monza",
                    driver_id="alonso",
                    constructor_id="ferrari",
                    grid_position=5,
                    finish_position=5,
                    status="finished",
                    points=10,
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


def test_driver_profile_success(client):
    response = client.get("/api/v1/drivers/verstappen")

    assert response.status_code == 200
    assert response.json() == {
        "driver_id": "verstappen",
        "name": "Max Verstappen",
        "nationality": "Dutch",
        "date_of_birth": "1997-09-30",
        "current_constructor_id": "red_bull",
        "career": {
            "wins": 63,
            "podiums": 112,
            "poles": 40,
            "championships": 4,
        },
    }


def test_driver_profile_404(client):
    response = client.get("/api/v1/drivers/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "driver missing not found"}


def test_driver_compare_season_head_to_head(client):
    response = client.get(
        "/api/v1/drivers/compare?driver_a=verstappen&driver_b=norris&season=2026"
    )

    assert response.status_code == 200
    assert response.json() == {
        "driver_a": "verstappen",
        "driver_b": "norris",
        "season": 2026,
        "head_to_head": {
            "qualifying_wins": {"verstappen": 1, "norris": 1},
            "race_finish_wins": {"verstappen": 1, "norris": 1},
            "points": {"verstappen": 25.0, "norris": 43.0},
        },
    }


def test_driver_compare_season_404_when_driver_did_not_race(client):
    response = client.get(
        "/api/v1/drivers/compare?driver_a=verstappen&driver_b=alonso&season=2026"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "driver alonso did not race in season 2026"}


def test_driver_compare_career_when_season_omitted(client):
    response = client.get("/api/v1/drivers/compare?driver_a=verstappen&driver_b=norris")

    assert response.status_code == 200
    assert response.json() == {
        "driver_a": "verstappen",
        "driver_b": "norris",
        "season": None,
        "head_to_head": {
            "qualifying_wins": {"verstappen": 1, "norris": 2},
            "race_finish_wins": {"verstappen": 1, "norris": 2},
            "points": {"verstappen": 43.0, "norris": 68.0},
        },
    }
