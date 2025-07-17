from datetime import datetime
from uuid import UUID

import time_machine
from fastapi.testclient import TestClient

from api.main import app
from bounded_contexts.game_and_stats.availability.schemas import (
    GamePlayersAvailabilityResponse,
)
from bounded_contexts.game_and_stats.game.schemas import (
    GamesPageResponse,
    GameResponse,
    NextGameResponse,
    LastGameResponse,
)
from bounded_contexts.game_and_stats.models import (
    AvailabilityStatus,
    StatOptions,
    GameResult,
)
from bounded_contexts.game_and_stats.stats.schemas import (
    GameStatsResponse,
    MonthTopScorerResponse,
)
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

    # Get games (without filters)
    response = client.post("/games/filter", json={})
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
    response = client.get(f"/stats/game/{game_id}")
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


def test_get_games_filtered(mock_user, mock_game_gen, mock_championship_gen):
    champ1 = mock_championship_gen(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 6, 1),
        is_league_format=True,
    )
    champ2 = mock_championship_gen(
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 6, 1),
        is_league_format=False,
    )

    game1 = mock_game_gen(
        championship_id=champ1.id,
        adversary="Adversary 1",
        date_hour=datetime(2024, 2, 1, 15, 0, 0),
        round=10,
        is_home=True,
        team_score=2,
        adversary_score=2,
        team_penalty_score=5,
        adversary_penalty_score=4,
    )
    game2 = mock_game_gen(
        championship_id=champ2.id,
        adversary="Adversary 2",
        date_hour=datetime(2025, 2, 1, 15, 0, 0),
        stage=StageOptions.QUARTAS_DE_FINAL,
        is_home=False,
        team_score=5,
        adversary_score=2,
    )
    game3 = mock_game_gen(
        championship_id=champ2.id,
        adversary="Adversary 3",
        date_hour=datetime(2025, 2, 8, 15, 0, 0),
        stage=StageOptions.SEMI_FINAL,
        is_home=True,
        is_wo=True,
        team_score=3,
        adversary_score=0,
    )

    data = {"adversary": "adver"}

    response = client.post("/games/filter", json=data)
    assert response.status_code == 200
    games = response.json()["items"]
    GameResponse.model_validate(games[0])
    assert len(games) == 3
    assert games[0]["id"] == str(game3.id)
    assert games[1]["id"] == str(game2.id)
    assert games[2]["id"] == str(game1.id)

    data["order_by"] = "date_hour_asc"
    response = client.post("/games/filter", json=data)
    games = response.json()["items"]
    assert games[0]["id"] == str(game1.id)
    assert games[1]["id"] == str(game2.id)
    assert games[2]["id"] == str(game3.id)

    data["date_hour_from"] = "2025-01-01T00:00:00"
    data["date_hour_to"] = "2025-02-02T00:00:00"
    response = client.post("/games/filter", json=data)
    games = response.json()["items"]
    assert len(games) == 1
    assert games[0]["id"] == str(game2.id)

    data = {"is_home": True, "order_by": "team_score_asc"}
    response = client.post("/games/filter", json=data)
    games = response.json()["items"]
    assert len(games) == 2
    assert games[0]["id"] == str(game1.id)
    assert games[1]["id"] == str(game3.id)

    data["is_wo"] = True
    response = client.post("/games/filter", json=data)
    games = response.json()["items"]
    assert len(games) == 1
    assert games[0]["id"] == str(game3.id)

    data = {"championship_id": str(champ2.id)}
    response = client.post("/games/filter", json=data)
    games = response.json()["items"]
    assert len(games) == 2
    assert games[0]["id"] == str(game3.id)
    assert games[1]["id"] == str(game2.id)

    data["stages"] = [StageOptions.QUARTAS_DE_FINAL, StageOptions.SEMI_FINAL]
    data["team_score_from"] = 3
    data["team_score_to"] = 5
    data["adversary_score_to"] = 2
    response = client.post("/games/filter", json=data)
    games = response.json()["items"]
    assert len(games) == 2
    assert games[0]["id"] == str(game3.id)
    assert games[1]["id"] == str(game2.id)

    data["adversary_score_from"] = 1
    response = client.post("/games/filter", json=data)
    games = response.json()["items"]
    assert len(games) == 1
    assert games[0]["id"] == str(game2.id)

    data = {"has_penalty_score": True}
    response = client.post("/games/filter", json=data)
    games = response.json()["items"]
    assert len(games) == 1
    assert games[0]["id"] == str(game1.id)


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


def test_delete_and_reactivate_game(
    mock_user_gen, mock_game, mock_game_player_stat, mock_game_player_availability
):
    mock_user_gen()

    delete_response = client.delete(f"/games/{mock_game.id}")
    assert delete_response.status_code == 204

    stats_response = client.get(f"/stats/game/{mock_game.id}")
    assert stats_response.status_code == 404
    availability_response = client.get(f"/player-availability/{mock_game.id}")
    assert availability_response.status_code == 404

    # Non super-admin user cannot reactivate
    reactivate_response = client.post(f"/games/reactivate/{mock_game.id}")
    assert reactivate_response.status_code == 403

    # Super-admin user can reactivate
    mock_user_gen(is_super_admin=True)
    reactivate_response = client.post(f"/games/reactivate/{mock_game.id}")
    assert reactivate_response.status_code == 201

    stats_response = client.get(f"/stats/game/{mock_game.id}")
    assert stats_response.status_code == 200
    availability_response = client.get(f"/player-availability/{mock_game.id}")
    assert availability_response.status_code == 200


def test_create_game_player_availability(mock_user_gen, mock_game, mock_player):
    mock_user_gen(player=mock_player)

    data = {
        "game_id": str(mock_game.id),
        "status": AvailabilityStatus.AVAILABLE,
    }

    response = client.post("/player-availability", json=data)
    assert response.status_code == 201


def test_error_create_game_player_availability(mock_user_gen, mock_game, mock_player):
    mock_user_gen()

    data = {
        "game_id": str(mock_game.id),
        "status": AvailabilityStatus.AVAILABLE,
    }

    response = client.post("/player-availability", json=data)
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Usuário precisa estar associado a um jogador para realizar esta ação. Acesse a página de usuários para fazer a associação."
    )


def test_get_game_players_availability(
    mock_user_gen, mock_game, mock_player_gen, mock_game_player_availability_gen
):
    player1 = mock_player_gen()
    player2 = mock_player_gen()
    player3 = mock_player_gen()

    mock_user_gen(player=player3)

    mock_game_player_availability_gen(
        player_id=player1.id, status=AvailabilityStatus.AVAILABLE
    )
    mock_game_player_availability_gen(
        player_id=player2.id, status=AvailabilityStatus.NOT_AVAILABLE
    )
    mock_game_player_availability_gen(
        player_id=player3.id, status=AvailabilityStatus.DOUBT
    )

    response = client.get(f"/player-availability/{mock_game.id}")
    assert response.status_code == 200
    response_body = response.json()
    GamePlayersAvailabilityResponse.model_validate(response_body)
    assert len(response_body["available"]) == 1
    assert len(response_body["not_available"]) == 1
    assert len(response_body["doubt"]) == 1
    assert response_body["current_player"] == AvailabilityStatus.DOUBT
    assert response_body["available"][0] == player1.name
    assert response_body["not_available"][0] == player2.name


def test_update_game_players_availability(
    mock_user_gen, mock_player, mock_game_player_availability
):
    mock_user_gen(player=mock_player)

    data = {"status": AvailabilityStatus.DOUBT}
    response = client.patch(
        f"/player-availability/{mock_game_player_availability.game_id}", json=data
    )
    assert response.status_code == 200


def test_delete_game_player_availability(
    mock_user_gen, mock_player, mock_game_player_availability
):
    mock_user_gen(player=mock_player)

    response = client.delete(
        f"/player-availability/{mock_game_player_availability.game_id}"
    )
    assert response.status_code == 204


@time_machine.travel("2025-01-01")
def test_get_next_game(mock_user, mock_game_gen, mock_championship_gen):
    # 1 - No next game
    response = client.get("/games/next-game")
    assert response.status_code == 200
    assert response.json() is None

    # 2 - With next game
    champ = mock_championship_gen(start_date=datetime(2025, 1, 1))
    game = mock_game_gen(
        championship_id=champ.id,
        adversary="Adversary Team",
        date_hour=datetime(2025, 1, 2, 15, 0, 0),
        stage=StageOptions.SEMI_FINAL,
    )

    response = client.get("/games/next-game")
    assert response.status_code == 200
    response_body = response.json()
    NextGameResponse.model_validate(response_body)
    assert response_body["id"] == str(game.id)
    assert response_body["championship_name"] == champ.name[:40]
    assert response_body["adversary"] == game.adversary[:30]
    assert response_body["date_hour"] == game.date_hour.isoformat()
    assert response_body["is_home"] == game.is_home
    assert response_body["confirmed_players"] == 0


@time_machine.travel("2025-01-17")
def test_get_month_top_scorer(
    mock_user,
    mock_player_gen,
    mock_game_player_stat_gen,
    mock_game_gen,
    mock_championship_gen,
):
    # 1 - No top scorer
    response = client.get("/stats/month-top-scorer")
    assert response.status_code == 200
    assert response.json() is None

    # 2 - With top scorer
    champ = mock_championship_gen(
        start_date=datetime(2025, 1, 1), end_date=datetime(2025, 6, 30)
    )
    game = mock_game_gen(
        championship_id=champ.id,
        date_hour=datetime(2025, 1, 15, 15, 0, 0),
        team_score=3,
    )

    player1 = mock_player_gen(name="Player 1", shirt_number=10)
    player2 = mock_player_gen(name="Player 2", shirt_number=9)

    mock_game_player_stat_gen(
        game_id=game.id,
        player_id=player1.id,
        stat=StatOptions.PLAYED,
    )
    mock_game_player_stat_gen(
        game_id=game.id,
        player_id=player2.id,
        stat=StatOptions.PLAYED,
    )
    mock_game_player_stat_gen(
        game_id=game.id,
        player_id=player1.id,
        stat=StatOptions.GOAL,
        quantity=1,
    )
    mock_game_player_stat_gen(
        game_id=game.id,
        player_id=player2.id,
        stat=StatOptions.GOAL,
        quantity=2,
    )

    response = client.get("/stats/month-top-scorer")
    assert response.status_code == 200
    response_body = response.json()
    MonthTopScorerResponse.model_validate(response_body)
    assert response_body["id"] == str(player2.id)
    assert response_body["name"] == player2.name
    assert response_body["image_url"] == player2.image_url
    assert response_body["shirt"] == player2.shirt_number
    assert response_body["goals"] == 2
    assert response_body["games_played"] == 1

    # 3 - Tie in goals, player with less games played wins
    game2 = mock_game_gen(
        championship_id=champ.id,
        date_hour=datetime(2025, 1, 16, 15, 0, 0),
        team_score=1,
    )
    mock_game_player_stat_gen(
        game_id=game2.id,
        player_id=player1.id,
        stat=StatOptions.PLAYED,
    )
    mock_game_player_stat_gen(
        game_id=game2.id,
        player_id=player1.id,
        stat=StatOptions.GOAL,
        quantity=1,
    )

    # player2 has 2 goals in 1 game, player1 has 2 goals in 2 games
    response = client.get("/stats/month-top-scorer")
    assert response.status_code == 200
    response_body = response.json()
    MonthTopScorerResponse.model_validate(response_body)
    assert response_body["id"] == str(player2.id)
    assert response_body["name"] == player2.name
    assert response_body["image_url"] == player2.image_url
    assert response_body["shirt"] == player2.shirt_number
    assert response_body["goals"] == 2
    assert response_body["games_played"] == 1


def test_get_last_games(mock_user, mock_game_gen):
    # 1 - No last games
    response = client.get("/games/last-games")
    assert response.status_code == 200
    assert response.json() is None

    # 2 - With 4 last games (bring all)
    game1 = mock_game_gen(
        adversary="Adversary 1",
        date_hour=datetime(2025, 1, 1),
        team_score=2,
        adversary_score=1,
    )
    game2 = mock_game_gen(
        adversary="Adversary 2",
        date_hour=datetime(2025, 1, 2),
        team_score=3,
        adversary_score=2,
    )
    game3 = mock_game_gen(
        adversary="Adversary 3",
        date_hour=datetime(2025, 1, 3),
        team_score=3,
        adversary_score=3,
    )
    game4 = mock_game_gen(
        adversary="Adversary 4",
        date_hour=datetime(2025, 1, 4),
        team_score=0,
        adversary_score=1,
    )

    response = client.get("/games/last-games")
    response_body = response.json()
    assert len(response_body) == 4
    LastGameResponse.model_validate(response_body[0])
    assert response_body[0]["id"] == str(game4.id)
    assert response_body[0]["result"] == GameResult.LOSS
    assert response_body[1]["id"] == str(game3.id)
    assert response_body[1]["result"] == GameResult.DRAW
    assert response_body[2]["id"] == str(game2.id)
    assert response_body[2]["result"] == GameResult.WIN
    assert response_body[3]["id"] == str(game1.id)
    assert response_body[3]["result"] == GameResult.WIN

    # 3 - With 6 games (bring 5 more recent)
    game5 = mock_game_gen(
        adversary="Adversary 5",
        date_hour=datetime(2025, 1, 5),
        team_score=1,
        adversary_score=1,
    )
    game6 = mock_game_gen(
        adversary="Adversary 6",
        date_hour=datetime(2025, 1, 6),
        team_score=4,
        adversary_score=5,
    )

    response = client.get("/games/last-games")
    response_body = response.json()
    assert len(response_body) == 5
    assert response_body[0]["id"] == str(game6.id)
    assert response_body[0]["result"] == GameResult.LOSS
    assert response_body[-1]["id"] == str(game2.id)
