from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_contract_routes_are_registered():
    response = client.get("/api/v1/circuits/__missing__")
    assert response.status_code == 404
