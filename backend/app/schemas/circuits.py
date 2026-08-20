from typing import Literal

from pydantic import BaseModel


class LapRecord(BaseModel):
    time: str
    driver_id: str
    year: int


class TechnicalCharacteristic(BaseModel):
    downforce_level: Literal["low", "medium", "high"] | None
    key_trait: str | None


class CircuitResponse(BaseModel):
    circuit_id: str
    name: str
    country: str
    locality: str
    length_km: float
    laps: int
    first_gp_year: int
    lap_record: LapRecord | None
    technical_characteristic: TechnicalCharacteristic
    trivia: list[str]
