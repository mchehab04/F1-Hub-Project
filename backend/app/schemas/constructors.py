from pydantic import BaseModel


class ConstructorCareer(BaseModel):
    wins: int
    podiums: int
    poles: int
    championships: int


class ConstructorProfileResponse(BaseModel):
    constructor_id: str
    name: str
    nationality: str
    current_drivers: list[str]
    career: ConstructorCareer


class ConstructorHeadToHead(BaseModel):
    race_wins: dict[str, int]
    points: dict[str, float]
    podiums: dict[str, int]


class ConstructorCompareResponse(BaseModel):
    constructor_a: str
    constructor_b: str
    season: int | None
    head_to_head: ConstructorHeadToHead
