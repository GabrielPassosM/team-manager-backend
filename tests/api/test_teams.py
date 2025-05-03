from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_create_team():
    data = {
        "name": "FC Barcelona",
        "emblem_url": "https://example.com/image.jpg",
        "foundation_date": "2023-01-01",
    }
    response = client.post("/teams", json=data)
    assert response.status_code == 201
    assert isinstance(response.json(), dict)
    assert "id" in response.json()


def test_get_team_by_id(mock_team):
    response = client.get(f"/teams/{str(mock_team.id)}")
    assert response.status_code == 200
    assert response.json()["name"] == "FC Barcelona"


def test_delete_team(mock_team):
    response = client.delete(f"/teams/{str(mock_team.id)}")
    assert response.status_code == 204

    response = client.get(f"/teams/{str(mock_team.id)}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Time não encontrado no sistema"
