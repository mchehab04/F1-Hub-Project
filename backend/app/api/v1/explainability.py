from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["model"])


@router.get("/models/{model_version}/explain")
def get_model_explanation(model_version: str):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")
