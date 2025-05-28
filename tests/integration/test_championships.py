from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient
import time_machine

from api.main import app
from bounded_contexts.championship.models import FinalStageOptions, ChampionshipStatus

client = TestClient(app)


@time_machine.travel("2025-01-01")
def test_create_championship(mock_user):
    data = {
        "name": "Copa do Mundo",
        "start_date": "2022-11-20",
        "end_date": "2022-12-18",
        "is_league_format": False,
        "final_stage": FinalStageOptions.CAMPEAO,
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
        final_stage=FinalStageOptions.QUARTAS_DE_FINAL,
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
