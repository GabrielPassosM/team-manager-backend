# tests/test_game_model.py

import pytest
from pydantic import ValidationError
from uuid import uuid4
from datetime import datetime

from bounded_contexts.game_and_stats.game.schemas import (
    GoalAndAssist,
    GameCreate,
    PlayerAndQuantity,
)

# --- Dados de Base para os Testes ---

PLAYER_1_ID = uuid4()
PLAYER_2_ID = uuid4()
PLAYER_3_ID = uuid4()


def get_base_data(**kwargs):
    """Cria um dicionário de dados válidos que pode ser sobrescrito."""
    data = {
        "championship_id": uuid4(),
        "adversary": "Corinthians",
        "date_hour": datetime.now(),
        "round": 1,
        "is_home": True,
        "team_score": 2,
        "adversary_score": 1,
        "players": [PLAYER_1_ID, PLAYER_2_ID],
        "goals_and_assists": [
            GoalAndAssist(goal_player_id=PLAYER_1_ID, assist_player_id=PLAYER_2_ID),
            GoalAndAssist(goal_player_id=PLAYER_2_ID),
        ],
    }
    data.update(kwargs)
    return data


# --- Testes Parametrizados ---


@pytest.mark.parametrize(
    "adversary_name, is_valid",
    [
        ("", False),  # Muito curto
        ("a" * 256, False),  # Muito longo
        ("Palmeiras", True),  # Válido
        ("São Paulo", True),  # Válido
    ],
)
def test_adversary_validation(adversary_name, is_valid):
    """Testa a validação do comprimento do nome do adversário."""
    data = get_base_data(adversary=adversary_name)
    if is_valid:
        GameCreate(**data)  # Não deve levantar exceção
    else:
        with pytest.raises(
            ValidationError,
            match="Adversary must be between 1 and 255 characters long.",
        ):
            GameCreate(**data)


@pytest.mark.parametrize(
    "round_num, is_valid",
    [(0, False), (10001, False), (1, True), (50, True), (None, True)],
)
def test_round_validation(round_num, is_valid):
    """Testa a validação do número da rodada."""
    data = get_base_data(round=round_num)
    if is_valid:
        GameCreate(**data)
    else:
        with pytest.raises(
            ValidationError, match="Round must be between 1 and 10000 if provided."
        ):
            GameCreate(**data)


def test_wo_logic_sanitization():
    """Testa se a lógica de W.O. é aplicada corretamente."""
    data = get_base_data(is_wo=True, team_score=None, adversary_score=None)
    game = GameCreate(**data)

    assert game.is_wo is True
    assert game.team_score == 3
    assert game.adversary_score == 0
    assert game.team_penalty_score is None
    assert game.adversary_penalty_score is None
    assert game.players is None
    assert game.goals_and_assists is None
    assert game.yellow_cards is None
    assert game.red_cards is None
    assert game.mvps is None


@pytest.mark.parametrize(
    "team_score, adversary_score, is_valid",
    [(1, None, False), (None, 1, False), (None, None, True), (2, 2, True)],
)
def test_score_pair_validation(team_score, adversary_score, is_valid):
    """Testa se os placares são fornecidos em pares."""
    data = get_base_data(
        team_score=team_score, adversary_score=adversary_score, goals_and_assists=None
    )
    if is_valid:
        GameCreate(**data)
    else:
        with pytest.raises(
            ValidationError,
            match="Must have both team_score and adversary_score or neither",
        ):
            GameCreate(**data)


@pytest.mark.parametrize(
    "team_penalty, adversary_penalty, is_valid",
    [(5, None, False), (None, 4, False), (None, None, True), (5, 4, True)],
)
def test_penalty_score_pair_validation(team_penalty, adversary_penalty, is_valid):
    """Testa se os placares de pênaltis são fornecidos em pares."""
    data = get_base_data(
        team_penalty_score=team_penalty, adversary_penalty_score=adversary_penalty
    )
    if is_valid:
        GameCreate(**data)
    else:
        with pytest.raises(
            ValidationError,
            match="Must have both team_penalty_score and adversary_penalty_score or neither",
        ):
            GameCreate(**data)


def test_player_list_sanitization():
    """Testa se jogadores duplicados são removidos da lista."""
    data = get_base_data(players=[PLAYER_1_ID, PLAYER_2_ID, PLAYER_1_ID])
    game = GameCreate(**data)
    assert len(game.players) == 2
    assert set(game.players) == {PLAYER_1_ID, PLAYER_2_ID}


@pytest.mark.parametrize(
    "score_field, value, is_valid, message",
    [
        ("team_score", -1, False, "Team score must be between 0 and 100 if provided."),
        ("team_score", 101, False, "Team score must be between 0 and 100 if provided."),
        (
            "adversary_score",
            -1,
            False,
            "Adversary score must be between 0 and 100 if provided.",
        ),
        (
            "adversary_score",
            101,
            False,
            "Adversary score must be between 0 and 100 if provided.",
        ),
        (
            "team_penalty_score",
            -1,
            False,
            "team_penalty_score must be between 0 and 100 if provided.",
        ),
        (
            "team_penalty_score",
            101,
            False,
            "team_penalty_score must be between 0 and 100 if provided.",
        ),
        (
            "adversary_penalty_score",
            -1,
            False,
            "adversary_penalty_score must be between 0 and 100 if provided.",
        ),
        (
            "adversary_penalty_score",
            101,
            False,
            "adversary_penalty_score must be between 0 and 100 if provided.",
        ),
    ],
)
def test_score_range_validation(score_field, value, is_valid, message):
    """Testa os limites de valor para todos os campos de placar."""
    data = get_base_data(
        goals_and_assists=None
    )  # Evita conflito com a contagem de gols
    # Ajusta placares para serem válidos antes de testar o campo específico
    if "penalty" in score_field:
        data.update({"team_penalty_score": 5, "adversary_penalty_score": 5})
    else:
        data.update({"team_score": 1, "adversary_score": 1})

    data[score_field] = value

    if is_valid:
        GameCreate(**data)
    else:
        with pytest.raises(ValidationError, match=message):
            GameCreate(**data)


@pytest.mark.parametrize(
    "stats_field", [("goals_and_assists"), ("yellow_cards"), ("red_cards"), ("mvps")]
)
def test_stats_require_players(stats_field):
    """Testa se a presença de estatísticas exige a lista de jogadores."""
    data = get_base_data(players=None)  # Remove os jogadores

    # Adiciona a estatística a ser testada
    if stats_field == "goals_and_assists":
        data[stats_field] = [GoalAndAssist(goal_player_id=PLAYER_1_ID)]
    elif stats_field == "red_cards":
        data[stats_field] = [PLAYER_1_ID]
    else:  # yellow_cards, mvps
        data[stats_field] = [PlayerAndQuantity(player_id=PLAYER_1_ID, quantity=1)]

    with pytest.raises(
        ValidationError, match="Players must be provided if any stats are included."
    ):
        GameCreate(**data)


def test_goals_and_assists_count_validation():
    """Testa se o número de gols corresponde ao placar do time."""
    data = get_base_data(
        team_score=3,
        adversary_score=0,
        goals_and_assists=[  # Apenas 2 gols, mas placar é 3
            GoalAndAssist(goal_player_id=PLAYER_1_ID),
            GoalAndAssist(goal_player_id=PLAYER_2_ID),
        ],
    )
    with pytest.raises(
        ValidationError, match="Can't have more goals and assists than team_score"
    ):
        GameCreate(**data)


@pytest.mark.parametrize(
    "goal, assist, is_valid, message",
    [
        (None, PLAYER_2_ID, False, "Can't assist an own goal"),
        (
            PLAYER_1_ID,
            PLAYER_1_ID,
            False,
            "Can't assist and score at the same time bro",
        ),
        (PLAYER_1_ID, PLAYER_2_ID, True, ""),
        (PLAYER_1_ID, None, True, ""),
    ],
)
def test_goal_and_assist_logic_validation(goal, assist, is_valid, message):
    """Testa a lógica interna de um gol e assistência."""
    data = get_base_data(
        team_score=1,
        adversary_score=0,
        players=[PLAYER_1_ID, PLAYER_2_ID],
        goals_and_assists=[GoalAndAssist(goal_player_id=goal, assist_player_id=assist)],
    )
    if is_valid:
        GameCreate(**data)
    else:
        with pytest.raises(ValidationError, match=message):
            GameCreate(**data)


def test_valid_data_passes():
    """Testa se um payload completamente válido passa sem erros."""
    data = get_base_data()
    try:
        GameCreate(**data)
    except ValidationError as e:
        pytest.fail(f"Dados válidos falharam na validação: {e}")
