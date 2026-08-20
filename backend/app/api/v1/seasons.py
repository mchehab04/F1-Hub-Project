from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["seasons"])


@router.get("/seasons")
def list_seasons():
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")


@router.get("/seasons/{season}/races")
def list_races(season: int):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")


@router.get("/seasons/{season}/accuracy")
def get_season_accuracy(season: int):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")
