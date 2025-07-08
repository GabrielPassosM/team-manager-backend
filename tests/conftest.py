from dataclasses import dataclass
from datetime import date, datetime
from random import randint
from uuid import uuid4, UUID

import pytest
from sqlmodel import select

from api.main import app
from bounded_contexts.championship.models import Championship
from bounded_contexts.game_and_stats.models import (
    Game,
    GamePlayerStat,
    StatOptions,
    GamePlayerAvailability,
    AvailabilityStatus,
)
from core.enums import StageOptions
from bounded_contexts.player.models import Player, PlayerPositions
from bounded_contexts.team.models import Team
from bounded_contexts.user.models import User
from core.services.auth import validate_user_token
from core.services.password import hash_password
from core.settings import FRIENDLY_CHAMPIONSHIP_NAME
from infra.database import get_session
from tests.database import (
    get_testing_session,
    init_test_db,
    remove_test_db,
    clean_db,  # import to make sure it runs
    TestingSessionLocal,
)


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


@pytest.fixture(scope="function")
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@dataclass
class _FakeUserForTokenValidation:
    id: UUID = uuid4()
    team_id: UUID = uuid4()
    name: str = "Test User"
    email: str = f"{uuid4()}@gmail.com"
    hashed_password: str = hash_password("1234")
    is_admin: bool = True
    is_super_admin: bool = False
    player_id: UUID | None = None
    player: Player | None = None


_fake_user = _FakeUserForTokenValidation()


# ------- TEST FIXTURES --------
@pytest.fixture(scope="function")
def mock_team(db_session):
    mock = Team(
        name="FC Barcelona",
        emblem_url="https://example.com/image.jpg",
        foundation_date=date(2023, 1, 1),
        season_start_date=date(2023, 1, 1),
        primary_color="#FF0000",
    )
    db_session.add(mock)
    db_session.commit()
    db_session.refresh(mock)

    _fake_user.team_id = mock.id

    yield mock


@pytest.fixture(scope="function")
def mock_team_gen(db_session, mock_team):
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
        db_session.add(mock)
        db_session.commit()
        db_session.refresh(mock)
        return mock

    yield _make_mock


@pytest.fixture(scope="function")
def mock_user(db_session, mock_team):
    id_email = uuid4()
    mock = User(
        team_id=mock_team.id,
        name="Test User",
        email=f"{id_email}@gmail.com",
        hashed_password=hash_password("1234"),
        is_admin=True,
    )
    db_session.add(mock)
    db_session.commit()
    db_session.refresh(mock)

    _fake_user.id = mock.id
    _fake_user.email = mock.email
    _fake_user.hashed_password = mock.hashed_password
    _fake_user.is_admin = mock.is_admin
    _fake_user.is_super_admin = mock.is_super_admin
    _fake_user.team_id = mock.team_id

    yield mock


@pytest.fixture(scope="function")
def mock_user_gen(db_session, mock_team):

    def _make_mock(
        name=None,
        email=None,
        password="1234",
        team_id=None,
        is_admin=True,
        is_super_admin=False,
        player: Player | None = None,
    ):
        player_id = player.id if player else None
        mock = User(
            team_id=team_id or mock_team.id,
            name=name or "Test User",
            email=email or f"{uuid4()}@gmail.com",
            hashed_password=hash_password(password),
            is_admin=is_admin,
            is_super_admin=is_super_admin,
            player_id=player_id,
        )
        db_session.add(mock)
        db_session.commit()
        db_session.refresh(mock)

        _fake_user.id = mock.id
        _fake_user.email = mock.email
        _fake_user.hashed_password = mock.hashed_password
        _fake_user.is_admin = mock.is_admin
        _fake_user.is_super_admin = mock.is_super_admin
        _fake_user.team_id = mock.team_id
        _fake_user.player_id = mock.player_id
        _fake_user.player = mock.player

        return mock

    yield _make_mock


@pytest.fixture(scope="function")
def mock_championship(db_session, mock_team):
    mock = Championship(
        team_id=mock_team.id,
        name=f"Campeonato {uuid4()}",
        start_date=date(2022, 11, 20),
        end_date=date(2022, 12, 18),
        is_league_format=False,
        final_stage=StageOptions.CAMPEAO,
    )
    db_session.add(mock)
    db_session.commit()
    db_session.refresh(mock)

    yield mock


@pytest.fixture(scope="function")
def mock_championship_gen(db_session, mock_team):
    def _make_mock(
        team_id: UUID = None,
        name: str = None,
        start_date: date = date(2022, 11, 20),
        end_date: date = None,
        is_league_format: bool = False,
        final_stage: StageOptions | None = None,
        final_position: int | None = None,
    ):
        mock = Championship(
            team_id=team_id or mock_team.id,
            name=name or f"Campeonato {uuid4()}",
            start_date=start_date,
            end_date=end_date,
            is_league_format=is_league_format,
            final_stage=final_stage,
            final_position=final_position,
        )
        db_session.add(mock)
        db_session.commit()
        db_session.refresh(mock)
        return mock

    yield _make_mock


@pytest.fixture(scope="function")
def mock_friendly_championship(db_session, mock_team):
    friendly_championship = db_session.exec(
        select(Championship).where(
            Championship.name == FRIENDLY_CHAMPIONSHIP_NAME,
            Championship.team_id == mock_team.id,
            Championship.deleted == False,
        )
    ).first()

    if friendly_championship:
        return friendly_championship

    mock = Championship(
        team_id=mock_team.id,
        name=FRIENDLY_CHAMPIONSHIP_NAME,
        start_date=date(2022, 11, 20),
        end_date=date(2022, 12, 18),
        is_league_format=False,
        final_stage=StageOptions.CAMPEAO,
    )
    db_session.add(mock)
    db_session.commit()
    db_session.refresh(mock)

    yield mock


@pytest.fixture(scope="function")
def mock_player(db_session, mock_team):
    mock = Player(
        team_id=mock_team.id,
        name=f"Jogador {uuid4()}",
        image_url="https://example.com/player.jpg",
        shirt_number=10,
        position=PlayerPositions.ATACANTE,
    )
    db_session.add(mock)
    db_session.commit()
    db_session.refresh(mock)

    yield mock


@pytest.fixture(scope="function")
def mock_player_gen(db_session, mock_team):
    def _make_mock(
        team_id: UUID = None,
        name: str = None,
        image_url: str = "https://example.com/player.jpg",
        shirt_number: int = None,
        position: PlayerPositions = PlayerPositions.ATACANTE,
    ):
        mock = Player(
            team_id=team_id or mock_team.id,
            name=name or f"Jogador {uuid4()}",
            image_url=image_url,
            shirt_number=shirt_number or randint(1, 99),
            position=position,
        )
        db_session.add(mock)
        db_session.commit()
        db_session.refresh(mock)
        return mock

    yield _make_mock


@pytest.fixture(scope="function")
def mock_game(db_session, mock_team, mock_championship):
    mock = Game(
        team_id=mock_team.id,
        championship_id=mock_championship.id,
        adversary=f"{uuid4()} FC",
        date_hour=datetime(2022, 11, 22, 19, 30),
        stage=StageOptions.FINAL,
        team_score=1,
        adversary_score=0,
    )
    db_session.add(mock)
    db_session.commit()
    db_session.refresh(mock)

    yield mock


@pytest.fixture(scope="function")
def mock_game_player_stat(db_session, mock_team, mock_game):
    mock = GamePlayerStat(
        team_id=mock_team.id,
        game_id=mock_game.id,
        stat=StatOptions.GOAL,
        quantity=1,
    )
    db_session.add(mock)
    db_session.commit()
    db_session.refresh(mock)

    yield mock


@pytest.fixture(scope="function")
def mock_game_player_availability(db_session, mock_team, mock_game, mock_player):
    mock = GamePlayerAvailability(
        team_id=mock_team.id,
        game_id=mock_game.id,
        player_id=mock_player.id,
        status=AvailabilityStatus.AVAILABLE,
    )
    db_session.add(mock)
    db_session.commit()
    db_session.refresh(mock)

    yield mock


@pytest.fixture(scope="function")
def mock_game_player_availability_gen(db_session, mock_team, mock_game, mock_player):
    def _make_mock(
        team_id: UUID = None,
        game_id: UUID = None,
        player_id: UUID = None,
        status: AvailabilityStatus = AvailabilityStatus.AVAILABLE,
    ):
        mock = GamePlayerAvailability(
            team_id=team_id or mock_team.id,
            game_id=game_id or mock_game.id,
            player_id=player_id or mock_player.id,
            status=status,
        )
        db_session.add(mock)
        db_session.commit()
        db_session.refresh(mock)
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
        is_super_admin=_fake_user.is_super_admin,
        player_id=_fake_user.player_id,
        player=_fake_user.player,
    )
