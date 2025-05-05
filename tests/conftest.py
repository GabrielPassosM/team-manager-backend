from uuid import uuid4

import pytest

from bounded_contexts.team.models import Team
from bounded_contexts.user.models import User
from bounded_contexts.user.service import _hash_password
from infra.database import get_session


@pytest.fixture(scope="function")
def mock_team():
    mock = Team(
        name="FC Barcelona",
        emblem_url="https://example.com/image.jpg",
        foundation_date="2023-01-01",
    )
    session = get_session()
    session.add(mock)
    session.commit()
    session.refresh(mock)
    yield mock


@pytest.fixture(scope="function")
def mock_user(mock_team):
    id_email = uuid4()
    mock = User(
        team_id=mock_team.id,
        name="Test User",
        email=f"{id_email}@gmail.com",
        hashed_password=_hash_password("1234"),
    )
    session = get_session()
    session.add(mock)
    session.commit()
    session.refresh(mock)

    yield mock


@pytest.fixture(scope="function")
def mock_user_gen(mock_team):
    def _make_mock():
        id_email = uuid4()
        mock = User(
            team_id=mock_team.id,
            name="Test User",
            email=f"{id_email}@gmail.com",
            hashed_password=_hash_password("1234"),
        )
        session = get_session()
        session.add(mock)
        session.commit()
        session.refresh(mock)
        return mock

    yield _make_mock
