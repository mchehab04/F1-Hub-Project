"""SQLAlchemy ORM tables. See docs/schema-design.md for the design rationale --
what's relational vs. JSON, and why there's no seasons/standings table."""

from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RaceStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    COMPLETED = "completed"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class DriverResultStatus(str, enum.Enum):
    FINISHED = "finished"
    DNF = "dnf"
    DSQ = "dsq"
    DNS = "dns"


class DownforceLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Constructor(Base):
    __tablename__ = "constructors"

    constructor_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    nationality: Mapped[str] = mapped_column(String, nullable=False)

    career_wins: Mapped[int] = mapped_column(Integer, default=0)
    career_podiums: Mapped[int] = mapped_column(Integer, default=0)
    career_poles: Mapped[int] = mapped_column(Integer, default=0)
    career_championships: Mapped[int] = mapped_column(Integer, default=0)


class Driver(Base):
    __tablename__ = "drivers"

    driver_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    nationality: Mapped[str] = mapped_column(String, nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    current_constructor_id: Mapped[str | None] = mapped_column(
        ForeignKey("constructors.constructor_id"), nullable=True
    )

    career_wins: Mapped[int] = mapped_column(Integer, default=0)
    career_podiums: Mapped[int] = mapped_column(Integer, default=0)
    career_poles: Mapped[int] = mapped_column(Integer, default=0)
    career_championships: Mapped[int] = mapped_column(Integer, default=0)


class Circuit(Base):
    __tablename__ = "circuits"

    circuit_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    locality: Mapped[str] = mapped_column(String, nullable=False)
    length_km: Mapped[float] = mapped_column(Float, nullable=False)
    laps: Mapped[int] = mapped_column(Integer, nullable=False)
    first_gp_year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Nullable together: no lap record yet (circuit's first-ever GP) -> all null,
    # API layer returns lap_record: null rather than a partially-filled object.
    lap_record_time: Mapped[str | None] = mapped_column(String, nullable=True)
    lap_record_driver_id: Mapped[str | None] = mapped_column(
        ForeignKey("drivers.driver_id"), nullable=True
    )
    lap_record_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    downforce_level: Mapped[str | None] = mapped_column(String, nullable=True)
    key_trait: Mapped[str | None] = mapped_column(String, nullable=True)

    trivia: Mapped[list[str]] = mapped_column(JSON, default=list)

    __table_args__ = (
        CheckConstraint(
            "downforce_level IS NULL OR downforce_level IN ('low','medium','high')",
            name="ck_circuits_downforce_level",
        ),
    )


class Race(Base):
    __tablename__ = "races"

    race_id: Mapped[str] = mapped_column(String, primary_key=True)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    circuit_id: Mapped[str] = mapped_column(ForeignKey("circuits.circuit_id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default=RaceStatus.UPCOMING.value)
    total_laps: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint("season", "round", name="uq_races_season_round"),
        Index("ix_races_season", "season"),
        CheckConstraint(
            "status IN ('upcoming','completed','postponed','cancelled')",
            name="ck_races_status",
        ),
    )


class RaceEntry(Base):
    """One row per driver per race. Backs race results, standings aggregation,
    and the accuracy tracker's actual-result side."""

    __tablename__ = "race_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    race_id: Mapped[str] = mapped_column(ForeignKey("races.race_id"), nullable=False)
    driver_id: Mapped[str] = mapped_column(ForeignKey("drivers.driver_id"), nullable=False)
    constructor_id: Mapped[str] = mapped_column(
        ForeignKey("constructors.constructor_id"), nullable=False
    )

    grid_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    finish_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    points: Mapped[float] = mapped_column(Float, default=0)

    __table_args__ = (
        UniqueConstraint("race_id", "driver_id", name="uq_race_entries_race_driver"),
        Index("ix_race_entries_driver_id", "driver_id"),
        Index("ix_race_entries_constructor_id", "constructor_id"),
        CheckConstraint(
            "status IS NULL OR status IN ('finished','dnf','dsq','dns')",
            name="ck_race_entries_status",
        ),
    )


class SessionWeather(Base):
    """Race-session weather, one row per race. FastF1-sourced, ~2018+ coverage."""

    __tablename__ = "session_weather"

    race_id: Mapped[str] = mapped_column(ForeignKey("races.race_id"), primary_key=True)
    weather_category: Mapped[str] = mapped_column(String, nullable=False)
    air_temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    track_temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class ReplayLap(Base):
    """Lap-by-lap position/gap data, one row per driver per lap per race.
    FastF1-sourced, reused directly for GET /races/{race_id}/replay."""

    __tablename__ = "replay_laps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    race_id: Mapped[str] = mapped_column(ForeignKey("races.race_id"), nullable=False)
    driver_id: Mapped[str] = mapped_column(ForeignKey("drivers.driver_id"), nullable=False)
    lap: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    gap_to_leader_s: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("race_id", "driver_id", "lap", name="uq_replay_laps_race_driver_lap"),
        Index("ix_replay_laps_race_id", "race_id"),
    )


class ModelVersion(Base):
    """Backs GET /models/{model_version}/explain. Feature importances are a
    global model property, not per-race -- one row per trained model version."""

    __tablename__ = "model_versions"

    model_version: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finish_position_feature_importances: Mapped[list[dict]] = mapped_column(
        JSON, nullable=False
    )
    dnf_feature_importances: Mapped[list[dict]] = mapped_column(JSON, nullable=False)


class Prediction(Base):
    """One row per (race, model_version). `inputs`/`predictions` are stored as
    JSON since they're always read/written whole, matching the API contract's
    nested shape 1:1 -- see docs/schema-design.md for why this isn't further
    normalized into child tables."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    race_id: Mapped[str] = mapped_column(ForeignKey("races.race_id"), nullable=False)
    model_version: Mapped[str] = mapped_column(
        ForeignKey("model_versions.model_version"), nullable=False
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    inputs: Mapped[dict] = mapped_column(JSON, nullable=False)
    predictions: Mapped[list[dict]] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        UniqueConstraint("race_id", "model_version", name="uq_predictions_race_model"),
    )
