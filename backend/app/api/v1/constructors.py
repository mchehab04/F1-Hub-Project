from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["constructors"])


# NOTE: /compare must be registered before /{constructor_id} so FastAPI
# doesn't match "compare" as a constructor_id path parameter.
@router.get("/constructors/compare")
def compare_constructors(constructor_a: str, constructor_b: str, season: int | None = None):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")


@router.get("/constructors/{constructor_id}")
def get_constructor(constructor_id: str):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")
