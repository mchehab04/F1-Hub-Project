from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["races"])


@router.get("/races/{race_id}")
def get_race(race_id: str):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")


@router.get("/races/{race_id}/prediction")
def get_prediction(race_id: str):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")


@router.get("/races/{race_id}/accuracy")
def get_race_accuracy(race_id: str):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")


@router.get("/races/{race_id}/replay")
def get_replay(race_id: str):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")
