from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient
import time_machine

from api.main import app
from bounded_contexts.championship.models import (
    ChampionshipStatus,
    ChampionshipFormats,
)
from core.enums import StageOptions
from bounded_contexts.championship.schemas import ChampionshipResponse
from core.settings import FRIENDLY_CHAMPIONSHIP_NAME

client = TestClient(app)


@time_machine.travel("2025-01-01")
def test_create_championship(mock_user):
    data = {
        "name": "Copa do Mundo",
        "start_date": "2022-11-20",
        "end_date": "2022-12-18",
        "is_league_format": False,
        "final_stage": StageOptions.CAMPEAO,
    }

    response = client.post("/championships", json=data)
    assert response.status_code == 201

    response_body = response.json()
    assert response_body["id"] is not None
    assert response_body["name"] == data["name"]
    assert response_body["start_date"] == data["start_date"]
    assert response_body["end_date"] == data["end_date"]
    assert response_body["is_league_format"] == data["is_league_format"]
    assert response_body["final_stage"] == data["final_stage"]
    assert response_body["final_position"] is None
    assert response_body["status"] == ChampionshipStatus.FINALIZADO

    response2 = client.post("/championships", json=data)
    assert response2.status_code == 400
    assert (
        response2.json()["detail"]
        == "Já existe um campeonato com este nome cadastrado no sistema"
    )


@time_machine.travel("2025-01-01")
def test_get_championships(mock_championship_gen):
    name_in_progress_champ = f"In progress {uuid4()}"
    mock_championship_gen(
        name=name_in_progress_champ,
        start_date=date(2024, 12, 15),
        end_date=date(2025, 1, 15),
    )
    name_finished_champ = f"Finished {uuid4()}"
    mock_championship_gen(
        name=name_finished_champ,
        start_date=date(2023, 12, 15),
        end_date=date(2024, 1, 15),
        final_stage=StageOptions.QUARTAS_DE_FINAL,
    )
    name_upcoming_champ = f"Upcoming {uuid4()}"
    mock_championship_gen(
        name=name_upcoming_champ, start_date=date(2025, 5, 1), end_date=date(2025, 6, 1)
    )
    name_in_progress_champ2 = f"In progress2 {uuid4()}"
    mock_championship_gen(
        name=name_in_progress_champ2,
        start_date=date(2024, 12, 25),
    )

    response = client.get("/championships")
    assert response.status_code == 200

    names_in_correct_order = [
        name_in_progress_champ2,
        name_in_progress_champ,
        name_upcoming_champ,
        name_finished_champ,
    ]

    response_body = response.json()
    assert len(response_body) == 4
    for index, champ in enumerate(response_body):
        assert champ["name"] == names_in_correct_order[index]


@time_machine.travel("2025-01-01")
def test_update_championship_success(mock_championship):
    champ_before_update = mock_championship

    data = {
        "name": f"NovoChamp {uuid4()}",
        "start_date": "2024-11-21",
        "end_date": "2025-01-21",
        "is_league_format": True,
        "final_stage": None,
        "final_position": None,
    }
    response = client.patch(f"/championships/{str(champ_before_update.id)}", json=data)
    assert response.status_code == 200

    response_body = response.json()
    ChampionshipResponse.model_validate(response_body)
    assert response_body["name"] == data["name"]
    assert response_body["start_date"] == data["start_date"]
    assert response_body["end_date"] == data["end_date"]
    assert response_body["is_league_format"] == data["is_league_format"]
    assert response_body["final_stage"] == data["final_stage"]
    assert response_body["final_position"] == data["final_position"]
    assert response_body["status"] == ChampionshipStatus.EM_ANDAMENTO


def test_error_update_championship_with_same_name(mock_championship_gen):
    champ1 = mock_championship_gen()
    champ2 = mock_championship_gen()

    data = {
        "name": champ1.name,
        "start_date": "2024-11-21",
        "end_date": "2025-01-21",
        "is_league_format": True,
        "final_stage": None,
        "final_position": None,
    }

    response = client.patch(f"/championships/{str(champ2.id)}", json=data)
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Já existe um campeonato com este nome cadastrado no sistema"
    )


def test_error_update_championship_friendly(mock_friendly_championship):
    data = {
        "name": "Editando Amistosos",
        "start_date": "2024-11-21",
        "is_league_format": True,
    }

    response = client.patch(
        f"/championships/{str(mock_friendly_championship.id)}", json=data
    )
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == f"Não é possível editar o campeonato {FRIENDLY_CHAMPIONSHIP_NAME}"
    )


def test_delete_championship(mock_championship):
    response = client.delete(f"/championships/{str(mock_championship.id)}")
    assert response.status_code == 204


def test_error_delete_championship_friendly(mock_friendly_championship):
    response = client.delete(f"/championships/{str(mock_friendly_championship.id)}")
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == f"Não é possível deletar o campeonato {FRIENDLY_CHAMPIONSHIP_NAME}"
    )


def test_error_delete_championship_with_games(mock_user, mock_championship, mock_game):
    response = client.delete(f"/championships/{str(mock_championship.id)}")
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Não é possível remover um campeonato com jogos atrelados a ele. Existe 1 jogo nessa situação. Por favor, remova-o antes de tentar novamente."
    )


@time_machine.travel("2025-01-01")
def test_filter_championships(clean_db, mock_championship_gen):
    champ1 = mock_championship_gen(
        name="Champ1", start_date=date(2024, 12, 15), end_date=date(2025, 1, 15)
    )
    champ2 = mock_championship_gen(
        name="2champ2",
        start_date=date(2023, 12, 15),
        end_date=date(2024, 1, 15),
        final_stage=StageOptions.QUARTAS_DE_FINAL,
    )
    champ3 = mock_championship_gen(
        start_date=date(2024, 1, 15),
        end_date=date(2024, 12, 15),
        is_league_format=True,
        final_position=5,
    )
    champ4 = mock_championship_gen(
        start_date=date(2025, 5, 1), end_date=date(2025, 6, 1)
    )

    data = {"name": "champ"}
    response = client.post("/championships/filter", json=data)
    assert response.status_code == 200
    response_body = response.json()
    assert len(response_body) == 2
    assert response_body[0]["id"] == str(champ1.id)
    assert response_body[1]["id"] == str(champ2.id)

    data["order_by"] = "start_date_asc"
    response = client.post("/championships/filter", json=data)
    response_body = response.json()
    assert len(response_body) == 2
    assert response_body[0]["id"] == str(champ2.id)
    assert response_body[1]["id"] == str(champ1.id)

    data["status"] = [ChampionshipStatus.EM_ANDAMENTO]
    response = client.post("/championships/filter", json=data)
    response_body = response.json()
    assert len(response_body) == 1
    assert response_body[0]["id"] == str(champ1.id)

    data = {
        "status": [ChampionshipStatus.FINALIZADO, ChampionshipStatus.NAO_INICIADO],
    }
    response = client.post("/championships/filter", json=data)
    response_body = response.json()
    assert len(response_body) == 3
    assert response_body[0]["id"] == str(champ2.id)
    assert response_body[1]["id"] == str(champ3.id)
    assert response_body[2]["id"] == str(champ4.id)

    data["format"] = ChampionshipFormats.LEAGUE
    response = client.post("/championships/filter", json=data)
    response_body = response.json()
    assert len(response_body) == 1
    assert response_body[0]["id"] == str(champ3.id)

    data["format"] = ChampionshipFormats.KNOCKOUT
    data["final_stages"] = [StageOptions.QUARTAS_DE_FINAL]
    response = client.post("/championships/filter", json=data)
    response_body = response.json()
    assert len(response_body) == 1
    assert response_body[0]["id"] == str(champ2.id)

    data = {
        "start_date_from": "2024-01-01",
        "end_date_from": "2025-01-01",
    }
    response = client.post("/championships/filter", json=data)
    response_body = response.json()
    assert len(response_body) == 2
    assert response_body[0]["id"] == str(champ1.id)
    assert response_body[1]["id"] == str(champ4.id)
