from fastapi.testclient import TestClient

from api.main import app
from bounded_contexts.terms_of_use.schemas import TermsOfUseResponse

client = TestClient(app, base_url="https://api.forquilha.app.br")


def test_verify_and_accept_terms_of_use_on_login(mock_user_gen, mock_terms_of_use_gen):
    mock_terms_of_use_gen(version=1, is_active=True)
    user = mock_user_gen(password="1234", accept_terms=False)

    data = {
        "username": user.email,
        "password": "1234",
    }
    response = client.post(f"/users/login", data=data)
    assert response.status_code == 200

    response_body = response.json()
    terms_version_to_accept = response_body.get("terms_version_to_accept")
    assert terms_version_to_accept == 1

    response = client.post(
        "/terms_of_use/accept",
        json={
            "terms_version": terms_version_to_accept,
            "user_id": str(user.id),
        },
    )
    assert response.status_code == 200

    response = client.post(f"/users/login", data=data)
    assert response.status_code == 200
    response_body = response.json()
    assert response_body["terms_version_to_accept"] is None


def test_get_active_terms_of_use(mock_terms_of_use_gen):
    mock_terms_of_use_gen(version=2, is_active=True)
    # The mock will deactivate the previous active terms
    active_terms = mock_terms_of_use_gen(
        version=3,
        is_active=True,
        content="These are the latest terms of use.",
    )

    response = client.get("/terms_of_use/active")
    assert response.status_code == 200

    response_body = response.json()
    TermsOfUseResponse.model_validate(response_body)
    assert response_body["version"] == active_terms.version
    assert response_body["content"] == active_terms.content
