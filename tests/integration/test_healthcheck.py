from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_database_startup_check():
    response = client.get("/database-check")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
