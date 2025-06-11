from uuid import uuid4

from fastapi.testclient import TestClient

from api.main import app
from bounded_contexts.user.models import User
from bounded_contexts.user.schemas import UserResponse, UserResponse
from core.services.password import verify_password

client = TestClient(app)


def test_create_user(mock_team, mock_player_gen):
    player = mock_player_gen()

    data = {
        "name": "Lionel Messi",
        "email": f"{uuid4()}@fcb.com",
        "password": "world-champion",
        "player_id": str(player.id),
    }
    response = client.post("/users", json=data)
    assert response.status_code == 201
    response_body = response.json()
    UserResponse.model_validate(response_body)


def test_error_create_user_with_long_password(mock_team):
    data = {
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
        "name": "Lionel Messi",
        "email": "messi@fcb.com",
        "password": "world-champion",
    }
    response = client.post("/users", json=data)
    assert response.status_code == 201

    data = {
        "name": "Neymar Jr.",
        "email": "messi@fcb.com",
        "password": "neymar",
    }
    response = client.post("/users", json=data)
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Já existe um usuário com este e-mail cadastrado no sistema"
    )


def test_get_user_by_id(mock_user):
    response = client.get(f"/users/{str(mock_user.id)}")
    assert response.status_code == 200

    response_body = response.json()
    assert response_body["is_admin"] == True
    User(**response_body)


def test_get_team_users(mock_user_gen, mock_team):
    user1 = mock_user_gen()
    user2 = mock_user_gen()
    assert user1.team_id == user2.team_id == mock_team.id

    response = client.get(f"/users/team-users")
    assert response.status_code == 200

    response_body = response.json()
    assert len(response_body) == 2
    [UserResponse.model_validate(user) for user in response_body]

    # First user should be the current user
    assert response_body[0]["id"] == str(user2.id)


def test_get_users_by_name_and_permission_type(mock_user_gen):
    user1 = mock_user_gen(name="Lionel Messi", is_admin=True)
    user2 = mock_user_gen(name="Neymar Jr.", is_admin=False)

    response1 = client.get(f"/users/name/onel?permission_type=")
    assert response1.status_code == 200
    response_body1 = response1.json()
    assert len(response_body1) == 1
    assert response_body1[0]["id"] == str(user1.id)

    response2 = client.get(f"/users/name/onel?permission_type=admin")
    assert response2.status_code == 200
    response_body2 = response2.json()
    assert len(response_body2) == 1
    assert response_body2[0]["id"] == str(user1.id)

    response3 = client.get(f"/users/name/onel?permission_type=user")
    assert response3.status_code == 200
    assert len(response3.json()) == 0

    response4 = client.get(f"/users/name/jr.?permission_type=user")
    assert response4.status_code == 200
    response_body4 = response4.json()
    assert len(response_body4) == 1
    assert response_body4[0]["id"] == str(user2.id)

    UserResponse.model_validate(response_body1[0])


def test_get_users_by_email_and_permission_type(mock_user_gen):
    user1 = mock_user_gen(email=f"messi@{uuid4()}.com", is_admin=True)
    user2 = mock_user_gen(email=f"neymar@{uuid4()}.com", is_admin=False)

    response1 = client.get(f"/users/email/messi?permission_type=")
    assert response1.status_code == 200
    response_body1 = response1.json()
    assert len(response_body1) == 1
    assert response_body1[0]["id"] == str(user1.id)

    response2 = client.get(f"/users/email/messi?permission_type=admin")
    assert response2.status_code == 200
    response_body2 = response2.json()
    assert len(response_body2) == 1
    assert response_body2[0]["id"] == str(user1.id)

    response3 = client.get(f"/users/email/messi?permission_type=user")
    assert response3.status_code == 200
    assert len(response3.json()) == 0

    response4 = client.get(f"/users/email/neymar?permission_type=user")
    assert response4.status_code == 200
    response_body4 = response4.json()
    assert len(response_body4) == 1
    assert response_body4[0]["id"] == str(user2.id)

    UserResponse.model_validate(response_body1[0])


def test_get_users_by_permission_type(mock_user_gen):
    user1 = mock_user_gen(is_admin=True)
    user2 = mock_user_gen(is_admin=False)
    user3 = mock_user_gen(is_admin=False)

    response1 = client.get(f"/users/type/admin")
    assert response1.status_code == 200
    response_body1 = response1.json()
    assert len(response_body1) == 1
    assert response_body1[0]["id"] == str(user1.id)

    response2 = client.get(f"/users/type/user")
    assert response2.status_code == 200
    response_body2 = response2.json()
    assert len(response_body2) == 2

    UserResponse.model_validate(response_body2[0])


def test_update_user_success(mock_user):
    user_before_update = mock_user

    data = {
        "name": "Lionel Messi",
        "email": f"{uuid4()}@fcb.com",
        "password": "world-champion",
    }
    response = client.patch(f"/users/{str(user_before_update.id)}", json=data)
    assert response.status_code == 200
    response_body = response.json()
    UserResponse.model_validate(response_body)
    assert response_body["name"] == data["name"]
    assert response_body["email"] == data["email"]
    assert response_body["is_admin"] == user_before_update.is_admin
    assert response_body["is_super_admin"] == user_before_update.is_super_admin
    assert not verify_password(data["password"], user_before_update.hashed_password)


def test_error_update_user_with_same_email(mock_user_gen):
    user1 = mock_user_gen()
    user2 = mock_user_gen()

    data = {
        "name": "Lionel Messi",
        "email": user1.email,
        "password": "world-champion",
    }
    response = client.patch(f"/users/{str(user2.id)}", json=data)
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Já existe um usuário com este e-mail cadastrado no sistema"
    )


def test_delete_user(mock_user_gen):
    user1 = mock_user_gen(is_admin=False)
    user2 = mock_user_gen()
    response = client.delete(f"/users/{str(user1.id)}")
    assert response.status_code == 204

    response = client.get(f"/users/{str(user1.id)}")
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
