from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["standings"])


@router.get("/standings/drivers")
def get_driver_standings(season: int):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")


@router.get("/standings/constructors")
def get_constructor_standings(season: int):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")
