from datetime import date
from typing import Literal

from pydantic import BaseModel


RaceStatus = Literal["upcoming", "completed", "postponed", "cancelled"]
DriverResultStatus = Literal["finished", "dnf", "dsq", "dns"]


class RaceResult(BaseModel):
    driver_id: str
    constructor_id: str
    constructor_name: str
    grid_position: int | None
    finish_position: int | None
    status: DriverResultStatus
    points: float


class RaceResponse(BaseModel):
    race_id: str
    round: int
    season: int
    name: str
    circuit_id: str
    date: date
    status: RaceStatus
    results: list[RaceResult] | None = None
