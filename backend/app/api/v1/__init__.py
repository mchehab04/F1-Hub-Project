from fastapi import APIRouter

from app.api.v1 import (
    circuits,
    constructors,
    drivers,
    explainability,
    races,
    seasons,
    standings,
)

api_router = APIRouter()
api_router.include_router(circuits.router)
api_router.include_router(seasons.router)
api_router.include_router(races.router)
api_router.include_router(explainability.router)
api_router.include_router(standings.router)
api_router.include_router(drivers.router)
api_router.include_router(constructors.router)
