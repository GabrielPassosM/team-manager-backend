from core import settings
from fastapi.testclient import TestClient
from api.main import app


client = TestClient(app)


def test_run_migrations():
    response = client.post(f"/admin/run-migrations/{settings.MIGRATIONS_PWD}")
    assert response.status_code == 200
    assert response.json() == {"message": "Migrations applied successfully"}


def test_get_pending_migrations():
    response = client.get(f"/admin/pending-migrations")
    assert response.status_code == 200
    response_data = response.json()
    assert "current_revision" in response_data
    assert response_data["pending"] == False
