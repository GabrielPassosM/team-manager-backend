from datetime import date

from fastapi.testclient import TestClient
from api.main import app
from bounded_contexts.team.schemas import RegisterTeamResponse
from core.settings import MIGRATIONS_PWD

client = TestClient(app)


def test_register_team_full_flow(mock_user_gen):
    mock_user_gen(is_super_admin=True)

    # 1 - Create intention to subscribe
    data = {
        "user_name": "John Doe",
        "user_email": "john@doe.com",
        "phone_number": "11999999999",
        "team_name": "Madureira FC",
    }

    response = client.post("/teams/intention-to-subscribe", json=data)
    assert response.status_code == 201

    # 2 - Create team based on intention to subscribe
    data = {"user_email": data["user_email"]}
    response = client.post(f"/admin/register-team/{MIGRATIONS_PWD}", json=data)
    assert response.status_code == 201

    response_data = response.json()
    RegisterTeamResponse.model_validate(response_data)
    assert response_data["client_user_email"] == data["user_email"]
    assert response_data["super_user_email"] == "superuser@madureirafc.com"


def test_renew_subscription(mock_user_gen, mock_team_gen):
    mock_user_gen(is_super_admin=True)
    team1 = mock_team_gen(name="Renew1", paid_until=date(2025, 9, 30))
    team2 = mock_team_gen(name="Renew2", paid_until=date(2025, 10, 15))

    data = {"team_ids": [str(team1.id), str(team2.id)], "months": 3}
    response = client.post("/admin/renew-subscription", json=data)
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data["renewed_info"]) == 2
    assert response_data["renewed_info"] == {
        "2025-12-30": ["Renew1"],
        "2026-01-15": ["Renew2"],
    }
