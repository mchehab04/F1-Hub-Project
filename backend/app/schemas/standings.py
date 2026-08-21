from pydantic import BaseModel


class DriverStanding(BaseModel):
    driver_id: str
    constructor_id: str
    constructor_name: str
    position: int
    points: float
    wins: int
    podiums: int
    trend: list[float]


class DriverStandingsResponse(BaseModel):
    season: int
    as_of_round: int
    standings: list[DriverStanding]


class ConstructorStanding(BaseModel):
    constructor_id: str
    position: int
    points: float
    wins: int
    podiums: int
    trend: list[float]


class ConstructorStandingsResponse(BaseModel):
    season: int
    as_of_round: int
    standings: list[ConstructorStanding]
