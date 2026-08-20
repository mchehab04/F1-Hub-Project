from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_contract_routes_are_registered():
    # Every route from docs/api-contract.md should exist, even as a 501 stub.
    response = client.get("/api/v1/circuits/bahrain")
    assert response.status_code == 501
