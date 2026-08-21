from datetime import date

from pydantic import BaseModel


class DriverCareer(BaseModel):
    wins: int
    podiums: int
    poles: int
    championships: int


class DriverProfileResponse(BaseModel):
    driver_id: str
    name: str
    nationality: str
    date_of_birth: date
    current_constructor_id: str | None
    career: DriverCareer


class DriverHeadToHead(BaseModel):
    qualifying_wins: dict[str, int]
    race_finish_wins: dict[str, int]
    points: dict[str, float]


class DriverCompareResponse(BaseModel):
    driver_a: str
    driver_b: str
    season: int | None
    head_to_head: DriverHeadToHead
