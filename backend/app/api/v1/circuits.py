from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["circuits"])


@router.get("/circuits/{circuit_id}")
def get_circuit(circuit_id: str):
    raise HTTPException(status_code=501, detail="Not implemented yet — see docs/api-contract.md")
