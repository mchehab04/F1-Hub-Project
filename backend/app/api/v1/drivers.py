from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["drivers"])


# NOTE: /compare must be registered before /{driver_id} so FastAPI doesn't
# match "compare" as a driver_id path parameter.
@router.get("/drivers/compare")
def compare_drivers(driver_a: str, driver_b: str, season: int | None = None):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")


@router.get("/drivers/{driver_id}")
def get_driver(driver_id: str):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")
