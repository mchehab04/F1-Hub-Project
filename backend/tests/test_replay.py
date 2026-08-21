from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.db.tables import Base, Driver, Race, RaceStatus, ReplayLap
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
                Driver(
                    driver_id="verstappen",
                    name="Max Verstappen",
                    nationality="Dutch",
                    date_of_birth=date(1997, 9, 30),
                ),
                Driver(
                    driver_id="leclerc",
                    name="Charles Leclerc",
                    nationality="Monegasque",
                    date_of_birth=date(1997, 10, 16),
                ),
                Race(
                    race_id="2026-bahrain",
                    season=2026,
                    round=1,
                    name="Bahrain Grand Prix",
                    circuit_id="bahrain",
                    date=date(2026, 3, 8),
                    status=RaceStatus.COMPLETED.value,
                    total_laps=3,
                ),
                Race(
                    race_id="2017-abu-dhabi",
                    season=2017,
                    round=20,
                    name="Abu Dhabi Grand Prix",
                    circuit_id="yas_marina",
                    date=date(2017, 11, 26),
                    status=RaceStatus.COMPLETED.value,
                    total_laps=55,
                ),
                Race(
                    race_id="2026-jeddah",
                    season=2026,
                    round=2,
                    name="Saudi Arabian Grand Prix",
                    circuit_id="jeddah",
                    date=date(2026, 3, 15),
                    status=RaceStatus.UPCOMING.value,
                    total_laps=50,
                ),
                Race(
                    race_id="2026-monza",
                    season=2026,
                    round=16,
                    name="Italian Grand Prix",
                    circuit_id="monza",
                    date=date(2026, 9, 6),
                    status=RaceStatus.COMPLETED.value,
                    total_laps=53,
                ),
            ]
        )
        db.flush()
        db.add_all(
            [
                ReplayLap(
                    race_id="2026-bahrain",
                    driver_id="verstappen",
                    lap=2,
                    position=1,
                    gap_to_leader_s=0.0,
                ),
                ReplayLap(
                    race_id="2026-bahrain",
                    driver_id="leclerc",
                    lap=2,
                    position=2,
                    gap_to_leader_s=1.8,
                ),
                ReplayLap(
                    race_id="2026-bahrain",
                    driver_id="verstappen",
                    lap=1,
                    position=1,
                    gap_to_leader_s=0.0,
                ),
                ReplayLap(
                    race_id="2026-bahrain",
                    driver_id="leclerc",
                    lap=1,
                    position=2,
                    gap_to_leader_s=1.2,
                ),
                ReplayLap(
                    race_id="2026-bahrain",
                    driver_id="verstappen",
                    lap=3,
                    position=1,
                    gap_to_leader_s=0.0,
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


def test_replay_success_groups_drivers_and_preserves_dnf_truncated_laps(client):
    response = client.get("/api/v1/races/2026-bahrain/replay")

    assert response.status_code == 200
    assert response.json() == {
        "race_id": "2026-bahrain",
        "total_laps": 3,
        "drivers": [
            {
                "driver_id": "leclerc",
                "laps": [
                    {"lap": 1, "position": 2, "gap_to_leader_s": 1.2},
                    {"lap": 2, "position": 2, "gap_to_leader_s": 1.8},
                ],
            },
            {
                "driver_id": "verstappen",
                "laps": [
                    {"lap": 1, "position": 1, "gap_to_leader_s": 0.0},
                    {"lap": 2, "position": 1, "gap_to_leader_s": 0.0},
                    {"lap": 3, "position": 1, "gap_to_leader_s": 0.0},
                ],
            },
        ],
    }


def test_replay_404_for_unknown_race_id(client):
    response = client.get("/api/v1/races/2026-missing/replay")

    assert response.status_code == 404
    assert response.json() == {"detail": "race not found"}


def test_replay_404_for_pre_2018_completed_race(client):
    response = client.get("/api/v1/races/2017-abu-dhabi/replay")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "no replay data available for races before 2018 (FastF1 coverage begins in 2018)"
    }


def test_replay_409_for_not_completed_race(client):
    response = client.get("/api/v1/races/2026-jeddah/replay")

    assert response.status_code == 409
    assert response.json() == {"detail": "race 2026-jeddah has not been completed yet"}


def test_replay_404_for_completed_post_2018_race_with_no_replay_laps(client):
    response = client.get("/api/v1/races/2026-monza/replay")

    assert response.status_code == 404
    assert response.json() == {"detail": "replay data not found for race 2026-monza"}
