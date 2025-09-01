from fastapi.testclient import TestClient
from api.main import app
from core.services.register_team_service import RegisterTeamResponse
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
    assert response_data["super_user_email"] == "madureirafc@superuser.com"
