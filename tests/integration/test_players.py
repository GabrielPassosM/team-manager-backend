from datetime import datetime

from fastapi.testclient import TestClient

from api.main import app
from bounded_contexts.game_and_stats.models import StatOptions
from bounded_contexts.player.models import PlayerPositions
from bounded_contexts.player.schemas import (
    PlayerResponse,
    PlayerWithoutUserResponse,
    PlayerNameAndShirt,
)
from core.enums import StageOptions
from core.settings import FRIENDLY_CHAMPIONSHIP_NAME

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
    assert response_body["has_before_system_stats"] is False
    PlayerResponse.model_validate(response_body)


def test_create_player_with_stats_before_system(
    mock_user, mock_before_system_championship, mock_friendly_championship
):
    data = {
        "name": "Ronaldinho",
        "image_url": "https://example.com/image.jpg",
        "shirt_number": 11,
        "position": PlayerPositions.FIXO,
        "played": 5,
        "goals": 10,
        "assists": 7,
        "yellow_cards": 6,
        "red_cards": 3,
        "mvps": 9,
    }

    response = client.post("/players", json=data)
    assert response.status_code == 201

    player_response_body = response.json()
    assert player_response_body["id"] is not None
    assert player_response_body["has_before_system_stats"] is True

    # Check that stats were created
    data_filter = {
        "players": [str(player_response_body["id"])],
    }
    response = client.post("/players/stats-filter", json=data_filter)
    assert response.status_code == 200

    stats_response_body = response.json()
    assert len(stats_response_body) == 1
    stats_info = stats_response_body[0]
    assert stats_info["id"] == player_response_body["id"]
    assert stats_info["played"] == data["played"]
    assert stats_info["goals"] == data["goals"]
    assert stats_info["assists"] == data["assists"]
    assert stats_info["yellow_cards"] == data["yellow_cards"]
    assert stats_info["red_cards"] == data["red_cards"]
    assert stats_info["mvps"] == data["mvps"]


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

    mock_game_player_stat_gen(
        player_id=player3.id, stat=StatOptions.YELLOW_CARD, quantity=2
    )

    response = client.get("/players")
    assert response.status_code == 200

    response_body = response.json()
    assert len(response_body) == 4  # the stat mock creates an extra player
    assert response_body[0]["id"] == str(player2.id)
    assert response_body[0]["has_before_system_stats"] is False
    assert response_body[1]["id"] == str(player1.id)
    assert response_body[2]["id"] == str(player3.id)
    assert response_body[2]["yellow_cards"] == 2
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


def test_add_before_system_stats_to_existing_player(
    mock_player, mock_before_system_championship, mock_friendly_championship
):
    player_before_update = mock_player

    update_data = {
        "name": "New Name2",
        "shirt_number": 10,
        "image_url": "test_image_url2.jpg",
        "position": PlayerPositions.PONTA,
        "played": 3,
        "goals": 5,
        "assists": 2,
        "yellow_cards": 2,
        "red_cards": 2,
        "mvps": 6,
    }

    response = client.patch(
        f"/players/{str(player_before_update.id)}", json=update_data
    )
    assert response.status_code == 200

    player_response_body = response.json()
    assert player_response_body["id"] == str(player_before_update.id)
    assert player_response_body["name"] == update_data["name"]
    assert player_response_body["shirt_number"] == update_data["shirt_number"]
    assert player_response_body["image_url"] == update_data["image_url"]
    assert player_response_body["position"] == update_data["position"]
    PlayerResponse.model_validate(player_response_body)

    # Check that stats were created
    data_filter = {
        "players": [str(player_response_body["id"])],
    }
    response = client.post("/players/stats-filter", json=data_filter)
    assert response.status_code == 200

    stats_response_body = response.json()
    assert len(stats_response_body) == 1
    stats_info = stats_response_body[0]
    assert stats_info["id"] == player_response_body["id"]
    assert stats_info["played"] == update_data["played"]
    assert stats_info["goals"] == update_data["goals"]
    assert stats_info["assists"] == update_data["assists"]
    assert stats_info["yellow_cards"] == update_data["yellow_cards"]
    assert stats_info["red_cards"] == update_data["red_cards"]
    assert stats_info["mvps"] == update_data["mvps"]


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


def test_get_players_filtered_by_stats(
    mock_player_gen, mock_game_player_stat_gen, mock_championship_gen, mock_game_gen
):
    player1 = mock_player_gen(name="Player 1", position=PlayerPositions.MEIO_CAMPO)
    player2 = mock_player_gen(name="Player 2", position=PlayerPositions.MEIO_CAMPO)
    player3 = mock_player_gen(name="Player 3", position=PlayerPositions.ATACANTE)

    champ1 = mock_championship_gen(
        name="Championship 1", start_date=datetime(2022, 1, 1)
    )
    game = mock_game_gen(
        championship_id=champ1.id,
        adversary="Adversary 1",
        date_hour=datetime(2022, 1, 21, 12, 0),
        stage=StageOptions.SEMI_FINAL,
    )

    mock_game_player_stat_gen(
        player_id=player1.id, stat=StatOptions.GOAL, quantity=1, game_id=game.id
    )
    mock_game_player_stat_gen(
        player_id=player2.id, stat=StatOptions.GOAL, quantity=2, game_id=game.id
    )
    mock_game_player_stat_gen(
        player_id=player3.id, stat=StatOptions.GOAL, quantity=3, game_id=game.id
    )
    mock_game_player_stat_gen(
        player_id=player1.id, stat=StatOptions.ASSIST, quantity=2, game_id=game.id
    )
    mock_game_player_stat_gen(
        player_id=player2.id, stat=StatOptions.ASSIST, quantity=3, game_id=game.id
    )

    mock_game_player_stat_gen(
        player_id=player1.id, stat=StatOptions.PLAYED, quantity=1, game_id=game.id
    )
    mock_game_player_stat_gen(
        player_id=player2.id, stat=StatOptions.PLAYED, quantity=1, game_id=game.id
    )
    mock_game_player_stat_gen(
        player_id=player3.id, stat=StatOptions.PLAYED, quantity=1, game_id=game.id
    )

    champ_friendly = mock_championship_gen(name=FRIENDLY_CHAMPIONSHIP_NAME)
    game = mock_game_gen(
        championship_id=champ_friendly.id,
        adversary="Adversary Friendly",
        date_hour=datetime(2023, 1, 20, 15, 0),
    )
    mock_game_player_stat_gen(
        player_id=player1.id, stat=StatOptions.GOAL, quantity=2, game_id=game.id
    )
    mock_game_player_stat_gen(
        player_id=player1.id, stat=StatOptions.ASSIST, quantity=2, game_id=game.id
    )
    mock_game_player_stat_gen(
        player_id=player1.id, stat=StatOptions.PLAYED, quantity=1, game_id=game.id
    )

    # 1 - Order by Goals desc, and exclude friendly (default)
    data = {
        "stat_name": StatOptions.GOAL,
    }
    response = client.post("/players/stats-filter", json=data)
    assert response.status_code == 200

    response_body = response.json()
    assert len(response_body) == 3
    PlayerResponse.model_validate(response_body[0])
    assert response_body[0]["id"] == str(player3.id)
    assert response_body[0]["goals"] == 3
    assert response_body[0]["played"] == 1
    assert response_body[1]["id"] == str(player2.id)
    assert response_body[1]["goals"] == 2
    assert response_body[1]["played"] == 1
    assert response_body[2]["id"] == str(player1.id)
    assert response_body[2]["goals"] == 1  # friendly game excluded
    assert response_body[2]["played"] == 1

    # 2 - Count friendly, quantity range and order by asc
    data = {
        "stat_name": StatOptions.GOAL,
        "order_by": "asc",
        "quantity_range": {"min": 3, "max": 10},
        "exclude_friendly": False,
    }
    response = client.post("/players/stats-filter", json=data)
    assert response.status_code == 200

    response_body = response.json()
    assert len(response_body) == 2
    # Order is asc. player1 has worse stats than player3 because he has more games
    assert response_body[0]["id"] == str(player1.id)
    assert response_body[0]["goals"] == 3
    assert response_body[0]["played"] == 2  # friendly game included
    assert response_body[1]["id"] == str(player3.id)
    assert response_body[1]["goals"] == 3
    assert response_body[1]["played"] == 1

    # 3 - Date range and player position filters (also PLAYED stat)
    data = {
        "stat_name": StatOptions.PLAYED,
        "date_range": {"start": "2022-01-15", "end": "2022-02-01"},
        "player_positions": [PlayerPositions.MEIO_CAMPO],
        "exclude_friendly": False,
    }
    response = client.post("/players/stats-filter", json=data)
    assert response.status_code == 200

    response_body = response.json()
    assert len(response_body) == 2
    assert response_body[0]["id"] == str(player1.id)
    assert response_body[0]["played"] == 1
    assert response_body[1]["id"] == str(player2.id)
    assert response_body[1]["played"] == 1

    # 4 - Championships, stages and specific players filters
    data = {
        "stat_name": StatOptions.ASSIST,
        "order_by": "desc",
        "championships": [str(champ1.id)],
        "stages": [StageOptions.SEMI_FINAL],
        "players": [str(player1.id), str(player2.id)],
        "exclude_friendly": False,
    }
    response = client.post("/players/stats-filter", json=data)
    assert response.status_code == 200

    response_body = response.json()
    assert len(response_body) == 2
    assert response_body[0]["id"] == str(player2.id)
    assert response_body[0]["assists"] == 3
    assert response_body[0]["played"] == 1
    assert response_body[1]["id"] == str(player1.id)
    assert response_body[1]["assists"] == 2
    assert response_body[1]["played"] == 1

    # 5 - No players matching filters
    data["stages"] = [StageOptions.FINAL]
    response = client.post("/players/stats-filter", json=data)
    assert response.status_code == 200

    response_body = response.json()
    assert len(response_body) == 0
    assert response_body == []
