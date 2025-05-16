from dataclasses import dataclass
from datetime import date
from uuid import uuid4, UUID

import pytest

from api.main import app
from bounded_contexts.team.models import Team
from bounded_contexts.user.models import User
from core.services.auth import validate_user_token
from core.services.password import hash_password
from infra.database import get_session
from tests.database import get_testing_session, init_test_db, remove_test_db


# -------- DB SETUP --------
@pytest.fixture(autouse=True)
def override_dependency():
    app.dependency_overrides[get_session] = get_testing_session
    app.dependency_overrides[validate_user_token] = _validate_user_token_testing
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_test_db()
    yield
    remove_test_db()


@dataclass
class _FakeUserForTokenValidation:
    id: UUID = uuid4()
    team_id: UUID = uuid4()
    name: str = "Test User"
    email: str = f"{uuid4()}@gmail.com"
    hashed_password: str = hash_password("1234")
    is_admin: bool = True


_fake_user = _FakeUserForTokenValidation()


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

    _fake_user.team_id = mock.id

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
        is_admin=True,
    )
    session = next(get_testing_session())
    session.add(mock)
    session.commit()
    session.refresh(mock)

    _fake_user.id = mock.id
    _fake_user.email = mock.email
    _fake_user.hashed_password = mock.hashed_password
    _fake_user.is_admin = mock.is_admin
    _fake_user.team_id = mock.team_id

    yield mock


@pytest.fixture(scope="function")
def mock_user_gen(mock_team):

    def _make_mock(
        name=None,
        email=None,
        password="1234",
        team_id=None,
        is_admin=True,
    ):
        mock = User(
            team_id=team_id or mock_team.id,
            name=name or "Test User",
            email=email or f"{uuid4()}@gmail.com",
            hashed_password=hash_password(password),
            is_admin=is_admin,
        )
        session = next(get_testing_session())
        session.add(mock)
        session.commit()
        session.refresh(mock)
        return mock

    yield _make_mock


def _validate_user_token_testing() -> User:
    return User(
        id=_fake_user.id,
        team_id=_fake_user.team_id,
        name=_fake_user.name,
        email=_fake_user.email,
        hashed_password=_fake_user.hashed_password,
        is_admin=_fake_user.is_admin,
    )
