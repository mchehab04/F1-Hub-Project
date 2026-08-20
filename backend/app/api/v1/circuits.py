from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.tables import Circuit
from app.schemas.circuits import CircuitResponse, LapRecord, TechnicalCharacteristic

router = APIRouter(tags=["circuits"])


@router.get("/circuits/{circuit_id}", response_model=CircuitResponse)
def get_circuit(circuit_id: str, db: Session = Depends(get_db)):
    circuit = db.get(Circuit, circuit_id)
    if circuit is None:
        raise HTTPException(status_code=404, detail="circuit not found")

    lap_record = None
    if circuit.lap_record_time is not None:
        lap_record = LapRecord(
            time=circuit.lap_record_time,
            driver_id=circuit.lap_record_driver_id,
            year=circuit.lap_record_year,
        )

    return CircuitResponse(
        circuit_id=circuit.circuit_id,
        name=circuit.name,
        country=circuit.country,
        locality=circuit.locality,
        length_km=circuit.length_km,
        laps=circuit.laps,
        first_gp_year=circuit.first_gp_year,
        lap_record=lap_record,
        technical_characteristic=TechnicalCharacteristic(
            downforce_level=circuit.downforce_level,
            key_trait=circuit.key_trait,
        ),
        trivia=circuit.trivia or [],
    )
