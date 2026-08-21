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
                    career_wins=118,
                    career_podiums=300,
                    career_poles=100,
                    career_championships=6,
                ),
                Constructor(
                    constructor_id="mclaren",
                    name="McLaren",
                    nationality="British",
                    career_wins=190,
                    career_podiums=520,
                    career_poles=160,
                    career_championships=8,
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
                ),
                Driver(
                    driver_id="perez",
                    name="Sergio Perez",
                    nationality="Mexican",
                    date_of_birth=date(1990, 1, 26),
                    current_constructor_id="red_bull",
                ),
                Driver(
                    driver_id="norris",
                    name="Lando Norris",
                    nationality="British",
                    date_of_birth=date(1999, 11, 13),
                    current_constructor_id="mclaren",
                ),
                Driver(
                    driver_id="piastri",
                    name="Oscar Piastri",
                    nationality="Australian",
                    date_of_birth=date(2001, 4, 6),
                    current_constructor_id="mclaren",
                ),
                Driver(
                    driver_id="leclerc",
                    name="Charles Leclerc",
                    nationality="Monegasque",
                    date_of_birth=date(1997, 10, 16),
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
                    driver_id="perez",
                    constructor_id="red_bull",
                    grid_position=4,
                    finish_position=4,
                    status="finished",
                    points=12,
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
                    race_id="2026-bahrain",
                    driver_id="piastri",
                    constructor_id="mclaren",
                    grid_position=3,
                    finish_position=3,
                    status="finished",
                    points=15,
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
                    driver_id="perez",
                    constructor_id="red_bull",
                    grid_position=4,
                    finish_position=3,
                    status="finished",
                    points=15,
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
                    race_id="2026-jeddah",
                    driver_id="piastri",
                    constructor_id="mclaren",
                    grid_position=2,
                    finish_position=2,
                    status="finished",
                    points=18,
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
                    driver_id="leclerc",
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


def test_constructor_profile_success(client):
    response = client.get("/api/v1/constructors/red_bull")

    assert response.status_code == 200
    assert response.json() == {
        "constructor_id": "red_bull",
        "name": "Red Bull Racing",
        "nationality": "Austrian",
        "current_drivers": ["perez", "verstappen"],
        "career": {
            "wins": 118,
            "podiums": 300,
            "poles": 100,
            "championships": 6,
        },
    }


def test_constructor_profile_404(client):
    response = client.get("/api/v1/constructors/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "constructor missing not found"}


def test_constructor_compare_season_independent_tallies(client):
    response = client.get(
        "/api/v1/constructors/compare?constructor_a=red_bull&constructor_b=mclaren&season=2026"
    )

    assert response.status_code == 200
    assert response.json() == {
        "constructor_a": "red_bull",
        "constructor_b": "mclaren",
        "season": 2026,
        "head_to_head": {
            "race_wins": {"red_bull": 1, "mclaren": 1},
            "points": {"red_bull": 52.0, "mclaren": 76.0},
            "podiums": {"red_bull": 2, "mclaren": 4},
        },
    }


def test_constructor_compare_season_404_when_constructor_did_not_compete(client):
    response = client.get(
        "/api/v1/constructors/compare?constructor_a=red_bull&constructor_b=ferrari&season=2026"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "constructor ferrari did not compete in season 2026"}


def test_constructor_compare_career_when_season_omitted(client):
    response = client.get(
        "/api/v1/constructors/compare?constructor_a=red_bull&constructor_b=mclaren"
    )

    assert response.status_code == 200
    assert response.json() == {
        "constructor_a": "red_bull",
        "constructor_b": "mclaren",
        "season": None,
        "head_to_head": {
            "race_wins": {"red_bull": 1, "mclaren": 2},
            "points": {"red_bull": 70.0, "mclaren": 101.0},
            "podiums": {"red_bull": 3, "mclaren": 5},
        },
    }
