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
