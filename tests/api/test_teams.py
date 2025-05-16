from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_create_team():
    data = {
        "name": "FC Barcelona",
        "emblem_url": "https://example.com/image.jpg",
        "foundation_date": "2023-01-01",
        "season_start_date": "2023-01-01",
        "season_end_date": "2023-12-31",
        "primary_color": "#FF0000",
    }
    response = client.post("/teams", json=data)
    assert response.status_code == 201

    response_body = response.json()
    assert response_body["id"] is not None
    assert response_body["name"] == "FC Barcelona"
    assert response_body["emblem_url"] == "https://example.com/image.jpg"
    assert response_body["foundation_date"] == "2023-01-01"
    assert response_body["season_start_date"] == "2023-01-01"
    assert response_body["season_end_date"] == "2023-12-31"
    assert response_body["primary_color"] == "#FF0000"
    assert response_body["paid_until"] is not None
    assert response_body["created_at"] is not None
    assert response_body["updated_at"] is not None
    assert response_body["deleted"] == False


def test_current_team(mock_team):
    response = client.get(f"/teams/me")
    assert response.status_code == 200
    assert response.json()["name"] == "FC Barcelona"


def test_delete_team(mock_team):
    response = client.delete(f"/teams/{str(mock_team.id)}")
    assert response.status_code == 204

    response = client.get(f"/teams/me")
    assert response.status_code == 404
    assert response.json()["detail"] == "Time não encontrado no sistema"
