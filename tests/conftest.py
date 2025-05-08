from datetime import date
from uuid import uuid4

import pytest

from api.main import app
from bounded_contexts.team.models import Team
from bounded_contexts.user.models import User
from bounded_contexts.user.service import _hash_password
from infra.database import get_session
from tests.database import get_testing_session, init_test_db, remove_test_db


# -------- DB SETUP --------
@pytest.fixture(autouse=True)
def override_dependency():
    app.dependency_overrides[get_session] = get_testing_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_test_db()
    yield
    remove_test_db()


# ------- TEST FIXTURES --------
@pytest.fixture(scope="function")
def mock_team():
    mock = Team(
        name="FC Barcelona",
        emblem_url="https://example.com/image.jpg",
        foundation_date=date(2023, 1, 1),
    )
    session = next(get_testing_session())
    session.add(mock)
    session.commit()
    session.refresh(mock)
    yield mock


@pytest.fixture(scope="function")
def mock_team_gen(mock_team):
    def _make_mock():
        mock = Team(
            name="FC Barcelona",
            emblem_url="https://example.com/image.jpg",
            foundation_date=date(2023, 1, 1),
        )
        session = next(get_testing_session())
        session.add(mock)
        session.commit()
        session.refresh(mock)
        return mock

    yield _make_mock


@pytest.fixture(scope="function")
def mock_user(mock_team):
    id_email = uuid4()
    mock = User(
        team_id=mock_team.id,
        name="Test User",
        email=f"{id_email}@gmail.com",
        hashed_password=_hash_password("1234"),
    )
    session = next(get_testing_session())
    session.add(mock)
    session.commit()
    session.refresh(mock)

    yield mock


@pytest.fixture(scope="function")
def mock_user_gen(mock_team):
    def _make_mock():
        mock = User(
            team_id=mock_team.id,
            name="Test User",
            email=f"{uuid4()}@gmail.com",
            hashed_password=_hash_password("1234"),
        )
        session = next(get_testing_session())
        session.add(mock)
        session.commit()
        session.refresh(mock)
        return mock

    yield _make_mock
