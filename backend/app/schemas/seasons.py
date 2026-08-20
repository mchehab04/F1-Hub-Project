from datetime import date
from typing import Literal

from pydantic import BaseModel


RaceStatus = Literal["upcoming", "completed", "postponed", "cancelled"]


class SeasonsResponse(BaseModel):
    seasons: list[int]


class SeasonRace(BaseModel):
    race_id: str
    round: int
    name: str
    circuit_id: str
    circuit_name: str
    date: date
    status: RaceStatus


class SeasonRacesResponse(BaseModel):
    season: int
    races: list[SeasonRace]
