from fastapi.testclient import TestClient

from api.main import app
from bounded_contexts.player.models import PlayerPositions
from bounded_contexts.player.schemas import PlayerResponse

client = TestClient(app)


def test_create_player(mock_user):
    data = {
        "name": "Copa do Mundo",
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


def test_get_players(mock_player_gen):
    player1 = mock_player_gen(name="B Player")
    player2 = mock_player_gen(name="A Player")
    player3 = mock_player_gen(name="C Player")

    response = client.get("/players")
    assert response.status_code == 200

    response_body = response.json()
    assert len(response_body) == 3
    assert response_body[0]["id"] == str(player2.id)
    assert response_body[1]["id"] == str(player1.id)
    assert response_body[2]["id"] == str(player3.id)
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


def test_delete_player(mock_player):
    response = client.delete(f"/players/{str(mock_player.id)}")
    assert response.status_code == 204


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
