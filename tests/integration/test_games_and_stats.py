from datetime import datetime
from uuid import UUID

from fastapi.testclient import TestClient

from api.main import app
from bounded_contexts.game_and_stats.game.schemas import GamesPageResponse, GameResponse
from bounded_contexts.game_and_stats.stats.schemas import GameStatsResponse
from core.enums import StageOptions

client = TestClient(app)


def test_create_and_get_game_and_stats(
    mock_user, mock_championship, mock_player_gen, mock_game_player_stat
):
    player1 = mock_player_gen()
    player2 = mock_player_gen()
    players = [player1, player2]

    data = {
        "championship_id": str(mock_championship.id),
        "adversary": "Adversary Team",
        "date_hour": "2022-11-21T14:00:00",
        "stage": StageOptions.SEMI_FINAL,
        "team_score": 3,
        "adversary_score": 1,
        "players": [str(p.id) for p in players],
        "goals_and_assists": [
            {"goal_player_id": str(player1.id), "assist_player_id": None},
            {"goal_player_id": str(player2.id), "assist_player_id": str(player1.id)},
            {"goal_player_id": None, "assist_player_id": None},  # own goal
        ],
        "yellow_cards": [
            {"player_id": str(player1.id), "quantity": 1},
        ],
        "red_cards": [str(player2.id)],
        "mvps": [
            {"player_id": str(player1.id), "quantity": 2},
        ],
    }

    # Create game
    response = client.post("/games", json=data)
    assert response.status_code == 201
    game_id = UUID(response.json())

    # Get games
    response = client.get("/games")
    assert response.status_code == 200
    response_body = response.json()
    GamesPageResponse.model_validate(response_body)
    assert response_body["total"] == 2
    assert response_body["limit"] == 5
    assert response_body["offset"] == 0
    items = response_body["items"]
    assert len(items) == 2
    GameResponse.model_validate(items[0])
    game = items[1]
    assert UUID(game["id"]) == game_id
    assert game["championship"]["id"] == str(mock_championship.id)
    assert game["championship"]["name"] == mock_championship.name[:40]
    assert game["adversary"] == data["adversary"]
    assert game["date_hour"] == data["date_hour"]
    assert game["stage"] == data["stage"]
    assert game["team_score"] == data["team_score"]
    assert game["adversary_score"] == data["adversary_score"]

    # Get game stats
    response = client.get(f"/stats/{game_id}")
    assert response.status_code == 200
    response_body = response.json()
    GameStatsResponse.model_validate(response_body)
    assert len(response_body["players"]) == 2
    assert isinstance(response_body["players"][0][0], str)
    assert isinstance(response_body["players"][0][1], int)
    assert isinstance(response_body["players"][0][2], str)
    assert len(response_body["goals_and_assists"]) == 3
    assert "player_name" in response_body["goals_and_assists"][0]
    assert "assist_player_name" in response_body["goals_and_assists"][0]
    assert (
        len(response_body["yellow_cards"])
        == len(response_body["red_cards"])
        == len(response_body["mvps"])
        == 1
    )
    assert response_body["yellow_cards"][0][1] == 1
    assert isinstance(response_body["red_cards"][0], str)
    assert response_body["mvps"][0][1] == 2


def test_error_create_game_invalid_championship(mock_user, mock_championship):
    # 1 - invalid format
    data = {
        "championship_id": str(mock_championship.id),
        "adversary": "Adversary Team",
        "date_hour": "2022-11-21T14:00:00",
        "round": 1,
    }

    response = client.post("/games", json=data)
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Etapa do jogo não compatível com tipo de campeonato (liga ou mata-mata)."
    )

    # 2 - date outside champ range
    data = {
        "championship_id": str(mock_championship.id),
        "adversary": "Adversary Team",
        "date_hour": "2025-11-21T14:00:00",
    }
    response = client.post("/games", json=data)
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "A data do jogo deve estar dentro da duração do campeonato (20/11/22 - 18/12/22)."
    )


def test_error_create_game_invalid_stats(mock_user, mock_championship, mock_player_gen):
    player1 = mock_player_gen()
    player2 = mock_player_gen()

    data = {
        "championship_id": str(mock_championship.id),
        "adversary": "Adversary Team",
        "date_hour": "2022-11-21T14:00:00",
        "stage": StageOptions.SEMI_FINAL,
        "team_score": 1,
        "adversary_score": 1,
        "players": [str(player2.id)],
        "goals_and_assists": [
            {"goal_player_id": str(player1.id), "assist_player_id": None}
        ],
    }
    response = client.post("/games", json=data)
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Jogador selecionado para estatística não está entre os jogadores da partida."
    )

    data["goals_and_assists"][0]["goal_player_id"] = str(player2.id)
    data["red_cards"] = [str(player1.id)]
    response = client.post("/games", json=data)
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Jogador selecionado para estatística não está entre os jogadores da partida."
    )

    data["red_cards"] = [str(player2.id)]
    data["yellow_cards"] = [{"player_id": str(player1.id), "quantity": 3}]
    response = client.post("/games", json=data)
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Jogador selecionado para estatística não está entre os jogadores da partida."
    )

    data["yellow_cards"][0]["player_id"] = str(player2.id)
    response = client.post("/games", json=data)
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Quantidade de cartões amarelos não pode ser maior que 2."
    )


def test_update_game_and_stats(
    mock_user, mock_game_player_stat, mock_championship_gen, mock_player_gen
):
    new_champ = mock_championship_gen()
    player = mock_player_gen()

    # 1 - Only game info
    data = {
        "championship_id": str(new_champ.id),
        "adversary": "New Adversary Team",
        "date_hour": "2022-11-21T14:00:00",
        "stage": StageOptions.SEMI_FINAL,
        "team_score": 3,
        "adversary_score": 1,
        "has_stats_update": False,
    }
    response = client.patch(f"/games/{mock_game_player_stat.game_id}", json=data)
    assert response.status_code == 200

    # 2 - Only stats
    data["has_stats_update"] = True
    stats_update = {
        "players": [str(player.id)],
        "goals_and_assists": [
            {"goal_player_id": str(player.id), "assist_player_id": None},
            {"goal_player_id": str(player.id), "assist_player_id": None},
            {"goal_player_id": str(player.id), "assist_player_id": None},
        ],
    }
    data = {**data, **stats_update}
    response = client.patch(f"/games/{mock_game_player_stat.game_id}", json=data)
    assert response.status_code == 200

    # 2 - Both game info and stats
    data["adversary_score"] = 2
    data["goals_and_assists"] = [
        {"goal_player_id": str(player.id), "assist_player_id": None},
        {"goal_player_id": str(player.id), "assist_player_id": None},
        {"goal_player_id": None, "assist_player_id": None},
    ]
    data["mvps"] = [{"player_id": str(player.id), "quantity": 2}]
    response = client.patch(f"/games/{mock_game_player_stat.game_id}", json=data)
    assert response.status_code == 200

    # Get game and stats updated on db
    response = client.get(f"/games/to-update/{mock_game_player_stat.game_id}")
    assert response.status_code == 200
    game_db = response.json()
    assert game_db["championship"]["id"] == str(data["championship_id"])
    assert game_db["adversary"] == data["adversary"]
    assert game_db["date_hour"] == data["date_hour"]
    assert game_db["stage"] == data["stage"]
    assert game_db["team_score"] == data["team_score"]
    assert game_db["adversary_score"] == data["adversary_score"]
    assert len(game_db["players"]) == 1
    assert game_db["players"] == [str(player.id)]
    assert len(game_db["goals_and_assists"]) == 3
    assert game_db["goals_and_assists"][0]["goal_player_id"] == str(player.id)
    assert game_db["goals_and_assists"][2]["goal_player_id"] is None
    assert len(game_db["mvps"]) == 1
    assert game_db["mvps"][0]["player_id"] == str(player.id)
    assert game_db["mvps"][0]["quantity"] == 2


def test_error_update_game_invalid_championship(
    mock_user, mock_game_player_stat, mock_championship_gen
):
    new_champ = mock_championship_gen(
        start_date=datetime(2022, 11, 20), end_date=datetime(2022, 12, 18)
    )

    # 1 - invalid format
    data = {
        "championship_id": str(new_champ.id),
        "adversary": "New Adversary Team",
        "date_hour": "2022-11-21T14:00:00",
        "round": 1,
        "has_stats_update": False,
    }
    response = client.patch(f"/games/{mock_game_player_stat.game_id}", json=data)
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Etapa do jogo não compatível com tipo de campeonato (liga ou mata-mata)."
    )

    # 2 - date outside champ range
    data = {
        "championship_id": str(new_champ.id),
        "adversary": "New Adversary Team",
        "date_hour": "2025-11-19T14:00:00",
        "has_stats_update": False,
    }
    response = client.patch(f"/games/{mock_game_player_stat.game_id}", json=data)
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "A data do jogo deve estar dentro da duração do campeonato (20/11/22 - 18/12/22)."
    )
