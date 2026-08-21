from pydantic import BaseModel


class ReplayLap(BaseModel):
    lap: int
    position: int
    gap_to_leader_s: float


class ReplayDriver(BaseModel):
    driver_id: str
    laps: list[ReplayLap]


class ReplayResponse(BaseModel):
    race_id: str
    total_laps: int
    drivers: list[ReplayDriver]
