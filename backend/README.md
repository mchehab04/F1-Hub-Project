# F1Hub backend

FastAPI service implementing [`docs/api-contract.md`](../docs/api-contract.md). Every route from the contract is registered and currently returns `501` — see `app/api/v1/` for the router stubs.

## Setup

```
cd backend
python -m venv .venv
.venv\Scripts\activate   # or `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
```

## Run

```
uvicorn app.main:app --reload
```

- API root: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Test

```
pytest
```

## Structure

- `app/api/v1/` — route handlers, one file per contract resource
- `app/db/` — SQLAlchemy engine/session + ORM tables (schema not designed yet)
- `app/schemas/` — Pydantic request/response models (not designed yet)
- `etl/` — batch data ingestion (Jolpica-F1 + FastF1), never called from the request path
- `ml/` — feature engineering, model training, prediction, and accuracy-metric computation
- `tests/` — pytest suite
