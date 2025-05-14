from datetime import date
from uuid import uuid4

import pytest

from api.main import app
from bounded_contexts.team.models import Team
from bounded_contexts.user.models import User
from core.services.password import hash_password
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
        season_start_date=date(2023, 1, 1),
        primary_color="#FF0000",
    )
    session = next(get_testing_session())
    session.add(mock)
    session.commit()
    session.refresh(mock)
    yield mock


@pytest.fixture(scope="function")
def mock_team_gen(mock_team):
    def _make_mock(
        name: str = None,
        emblem_url: str = None,
        foundation_date: date = None,
        paid_until: date = None,
        season_start_date: date = None,
        season_end_date: date = None,
        primary_color: str = None,
    ):
        mock = Team(
            name=name or "FC Barcelona",
            emblem_url=emblem_url or "https://example.com/image.jpg",
            foundation_date=foundation_date or date(2023, 1, 1),
            paid_until=paid_until,
            season_start_date=season_start_date or date(2023, 1, 1),
            season_end_date=season_end_date,
            primary_color=primary_color or "#FF0000",
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
        hashed_password=hash_password("1234"),
    )
    session = next(get_testing_session())
    session.add(mock)
    session.commit()
    session.refresh(mock)

    yield mock


@pytest.fixture(scope="function")
def mock_user_gen(mock_team):

    def _make_mock(
        name=None,
        email=None,
        password="1234",
        team_id=None,
    ):
        mock = User(
            team_id=team_id or mock_team.id,
            name=name or "Test User",
            email=email or f"{uuid4()}@gmail.com",
            hashed_password=hash_password(password),
        )
        session = next(get_testing_session())
        session.add(mock)
        session.commit()
        session.refresh(mock)
        return mock

    yield _make_mock
