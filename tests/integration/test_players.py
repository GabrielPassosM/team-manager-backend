from uuid import uuid4

from fastapi.testclient import TestClient

from api.main import app
from bounded_contexts.game_and_stats.models import StatOptions
from bounded_contexts.player.models import PlayerPositions
from bounded_contexts.player.schemas import (
    PlayerResponse,
    PlayerWithoutUserResponse,
    PlayerNameAndShirt,
)

client = TestClient(app)


def test_create_player(mock_user):
    data = {
        "name": "Ronaldinho",
        "image_url": "https://example.com/image.jpg",
        "shirt_number": 11,
        "position": PlayerPositions.FIXO,
    }

    response = client.post("/players", json=data)
    assert response.status_code == 201

    response_body = response.json()
    assert response_body["id"] is not None
    assert response_body["name"] == data["name"]
    assert response_body["image_url"] == data["image_url"]
    assert response_body["shirt_number"] == data["shirt_number"]
    assert response_body["position"] == data["position"]
    PlayerResponse.model_validate(response_body)


def test_error_create_player_max_players(mock_team_gen, mock_user_gen, mock_player_gen):
    team = mock_team_gen(max_players_or_users=2)
    team_id = team.id
    mock_user_gen(team_id=team_id, is_admin=True)
    mock_player_gen(team_id=team_id)
    mock_player_gen(team_id=team_id)

    data = {
        "name": "Ronaldinho",
        "image_url": "https://example.com/image.jpg",
        "shirt_number": 11,
        "position": PlayerPositions.FIXO,
    }

    response = client.post("/players", json=data)
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "O número máximo de jogadores do time foi atingido. Atualize seu plano para adicionar mais jogadores."
    )


def test_create_player_for_non_admin_user(mock_user_gen, mock_player_gen):
    player = mock_player_gen()

    # 1 - Non-admin user without player can create a player
    mock_user_gen(is_admin=False)
    data = {
        "name": "Iniesta",
        "shirt_number": 8,
        "position": PlayerPositions.MEIO_CAMPO,
    }
    response = client.post("/players", json=data)
    assert response.status_code == 201

    # 2 - Non-admin user with player cannot create another player
    mock_user_gen(is_admin=False, player=player)
    data = {
        "name": "Xavi",
        "shirt_number": 6,
        "position": PlayerPositions.MEIO_CAMPO,
    }
    response = client.post("/players", json=data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Usuário não possui permissão para essa ação."

    # clean current_user for next tests
    mock_user_gen()


def test_get_players(mock_player_gen, mock_game_player_stat_gen):
    player1 = mock_player_gen(name="B Player")
    player2 = mock_player_gen(name="A Player")
    player3 = mock_player_gen(name="C Player")

    mock_game_player_stat_gen(player_id=player3.id, stat=StatOptions.GOAL)

    response = client.get("/players")
    assert response.status_code == 200

    response_body = response.json()
    assert len(response_body) == 4  # the stat mock creates an extra player
    assert response_body[0]["id"] == str(player2.id)
    assert response_body[1]["id"] == str(player1.id)
    assert response_body[2]["id"] == str(player3.id)
    assert response_body[2]["goals"] == 1
    PlayerResponse.model_validate(response_body[0])


def test_update_player(mock_player):
    player_before_update = mock_player

    update_data = {
        "name": "New Name",
        "shirt_number": 9,
        "image_url": "test_image_url.jpg",
        "position": PlayerPositions.ALA,
    }

    response = client.patch(
        f"/players/{str(player_before_update.id)}", json=update_data
    )
    assert response.status_code == 200

    response_body = response.json()
    assert response_body["id"] == str(player_before_update.id)
    assert response_body["name"] == update_data["name"]
    assert response_body["shirt_number"] == update_data["shirt_number"]
    assert response_body["image_url"] == update_data["image_url"]
    assert response_body["position"] == update_data["position"]
    PlayerResponse.model_validate(response_body)


def test_non_admin_user_update_player(mock_player_gen, mock_user_gen):
    # 1 - Non-admin user can update their own player
    player = mock_player_gen()
    mock_user_gen(is_admin=False, player=player)

    update_data = {
        "name": "Updated Player A",
        "shirt_number": 10,
        "image_url": "updated_image_url.jpg",
        "position": PlayerPositions.FIXO,
    }

    response = client.patch(f"/players/{str(player.id)}", json=update_data)
    assert response.status_code == 200

    # 2 - Non-admin user cannot update another player's data
    mock_user_gen(is_admin=False)
    response = client.patch(f"/players/{str(player.id)}", json=update_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Usuário não possui permissão para essa ação."

    # clean current_user for next tests
    mock_user_gen()


def test_delete_player(mock_player):
    response = client.delete(f"/players/{str(mock_player.id)}")
    assert response.status_code == 204


def test_non_admin_user_delete_player(mock_player_gen, mock_user_gen):
    # 1 - Non-admin user can delete their own player
    player = mock_player_gen()
    mock_user_gen(is_admin=False, player=player)

    response = client.delete(f"/players/{str(player.id)}")
    assert response.status_code == 204

    # 2 - Non-admin user cannot delete another player's data
    mock_user_gen(is_admin=False)
    response = client.delete(f"/players/{str(player.id)}")
    assert response.status_code == 403
    assert response.json()["detail"] == "Usuário não possui permissão para essa ação."

    # clean current_user for next tests
    mock_user_gen()


def test_filter_players(mock_player_gen):
    player1 = mock_player_gen(
        name="Player A", shirt_number=10, position=PlayerPositions.FIXO
    )
    player2 = mock_player_gen(
        name="Player B", shirt_number=11, position=PlayerPositions.ZAGUEIRO
    )
    player3 = mock_player_gen(
        name="Player C", shirt_number=12, position=PlayerPositions.ZAGUEIRO
    )

    data = {"name": "player"}

    response = client.post("/players/filter", json=data)
    assert response.status_code == 200
    response_body = response.json()
    assert len(response_body) == 3
    assert response_body[0]["id"] == str(player1.id)
    assert response_body[1]["id"] == str(player2.id)
    assert response_body[2]["id"] == str(player3.id)

    data["order_by"] = "name_desc"
    response = client.post("/players/filter", json=data)
    response_body = response.json()
    assert len(response_body) == 3
    assert response_body[0]["id"] == str(player3.id)
    assert response_body[1]["id"] == str(player2.id)
    assert response_body[2]["id"] == str(player1.id)

    data["positions"] = [PlayerPositions.ZAGUEIRO]
    response = client.post("/players/filter", json=data)
    response_body = response.json()
    assert len(response_body) == 2
    assert response_body[0]["id"] == str(player3.id)
    assert response_body[1]["id"] == str(player2.id)

    data["shirt_number"] = 11
    response = client.post("/players/filter", json=data)
    response_body = response.json()
    assert len(response_body) == 1
    assert response_body[0]["id"] == str(player2.id)


def test_get_players_without_user(mock_player_gen, mock_user_gen):
    player1 = mock_player_gen(name="Player A")
    player2 = mock_player_gen(name="Player B")

    mock_user_gen(player=player1)

    response = client.get("/players/without-user")
    assert response.status_code == 200

    response_body = response.json()
    assert len(response_body) == 1
    assert response_body[0]["id"] == str(player2.id)
    PlayerWithoutUserResponse.model_validate(response_body[0])


def test_get_players_name_and_shirt(mock_player_gen, mock_user):
    player1 = mock_player_gen(name="Player B", shirt_number=10)
    player2 = mock_player_gen(name="Player A", shirt_number=11)

    response = client.get("/players/all-name-and-shirt")
    assert response.status_code == 200

    response_body = response.json()
    assert len(response_body) == 2
    assert response_body[0]["id"] == str(player2.id)
    PlayerNameAndShirt.model_validate(response_body[0])
