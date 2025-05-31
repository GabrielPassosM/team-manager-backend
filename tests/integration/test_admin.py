from uuid import uuid4

from core import settings
from fastapi.testclient import TestClient
from api.main import app


client = TestClient(app)


# def test_run_migrations():
#     response = client.post(f"/admin/run-migrations/{settings.MIGRATIONS_PWD}")
#     assert response.status_code == 200
#     assert response.json() == {"message": "Migrations applied successfully"}
#
#
# def test_get_pending_migrations():
#     response = client.get(f"/admin/pending-migrations")
#     assert response.status_code == 200
#     response_data = response.json()
#     assert "current_revision" in response_data
#     assert response_data["pending"] == False


def test_register_new_team(mock_user_gen):
    mock_user_gen(is_super_admin=True)

    data = {
        "name": "FC Barcelona",
        "emblem_url": "https://example.com/image.jpg",
        "foundation_date": "2023-01-01",
        "season_start_date": "2023-01-01",
        "season_end_date": "2023-12-31",
        "primary_color": "#FF0000",
        "paid_until": "2024-01-01",
        "user_email": "superuser@fcbarcelona.com",
        "user_password": "123456789",
    }
    response = client.post(f"/admin/register-team/{settings.MIGRATIONS_PWD}", json=data)
    assert response.status_code == 201

    response_body = response.json()
    assert response_body["team"] is not None
    assert response_body["super_user"] is not None
    assert response_body["friendly_championship"] is not None


def test_create_team_base_models(mock_user_gen, mock_team):
    mock_user_gen(is_super_admin=True)

    data = {
        "name": "Whatever",
        "team_id": str(mock_team.id),
        "user_email": f"{uuid4()}@example.com",
        "user_password": "123456789",
    }
    response = client.post(f"/admin/register-team/{settings.MIGRATIONS_PWD}", json=data)
    assert response.status_code == 201

    response_body = response.json()
    assert response_body["team"] == str(mock_team.id)
    assert response_body["super_user"] is not None
    assert response_body["friendly_championship"] is not None
