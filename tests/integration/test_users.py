from uuid import uuid4

from fastapi.testclient import TestClient

from api.main import app
from bounded_contexts.user.models import User
from bounded_contexts.user.schemas import UserResponse, UserResponse

client = TestClient(app)


def test_create_user(mock_team):
    data = {
        "team_id": str(mock_team.id),
        "name": "Lionel Messi",
        "email": f"{uuid4()}@fcb.com",
        "password": "world-champion",
    }
    response = client.post("/users", json=data)
    assert response.status_code == 201
    assert isinstance(response.json(), dict)
    assert "id" in response.json()


def test_error_create_user_with_long_password(mock_team):
    data = {
        "team_id": str(mock_team.id),
        "name": "Dummy",
        "email": f"{uuid4()}@fcb.com",
        "password": "1234" * 19,  # 76 characters
    }
    response = client.post("/users", json=data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Senha deve ter no máximo 72 caracteres"


def test_error_create_duplicate_user_email(mock_team_gen):
    team1 = mock_team_gen()
    team2 = mock_team_gen()

    data = {
        "team_id": str(team1.id),
        "name": "Lionel Messi",
        "email": "messi@fcb.com",
        "password": "world-champion",
    }
    response = client.post("/users", json=data)
    assert response.status_code == 201

    data = {
        "team_id": str(team2.id),
        "name": "Neymar Jr.",
        "email": "messi@fcb.com",
        "password": "neymar",
    }
    response = client.post("/users", json=data)
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Já existe um usuário com este e-mail cadastrado neste time no sistema"
    )


def test_get_user_by_id(mock_user):
    response = client.get(f"/users/{str(mock_user.id)}")
    assert response.status_code == 200

    response_body = response.json()
    assert response_body["is_admin"] == True
    User(**response_body)


def test_get_users_by_team_id(mock_user_gen, mock_team):
    user1 = mock_user_gen()
    user2 = mock_user_gen()
    assert user1.team_id == user2.team_id == mock_team.id

    response = client.get(f"/users/team/{str(user1.team_id)}")
    assert response.status_code == 200

    response_body = response.json()
    assert len(response_body) == 2
    [UserResponse.model_validate(user) for user in response_body]


def test_delete_user(mock_user):
    response = client.delete(f"/users/{str(mock_user.id)}")
    assert response.status_code == 204

    response = client.get(f"/users/{str(mock_user.id)}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuário não encontrado no sistema"


def test_login_success(mock_user_gen):
    user = mock_user_gen(password="1234")
    data = {
        "username": user.email,
        "password": "1234",
    }
    response = client.post(f"/users/login", data=data)
    assert response.status_code == 200

    response_body = response.json()
    assert "access_token" in response_body

    UserResponse.model_validate(response_body["user"])


def test_login_fail(mock_user_gen):
    user = mock_user_gen(password="1234")
    data = {
        "username": user.email,
        "password": "wrong-password",
    }
    response = client.post(f"/users/login", data=data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Email ou senha incorretos"


def test_get_current_user(mock_user):
    response = client.get("/users/me")
    assert response.status_code == 200

    response_body = response.json()
    UserResponse.model_validate(response_body)
