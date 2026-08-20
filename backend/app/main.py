from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.db.session import engine
from app.db.tables import Base

# No migrations tool for v1 (solo, local-only) -- create_all() is enough.
# Revisit with Alembic if the schema needs to evolve after real data exists.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="F1Hub API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health():
    return {"status": "ok"}
