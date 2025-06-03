from datetime import date
from uuid import uuid4

from sqlmodel import select

from bounded_contexts.championship.models import Championship, FinalStageOptions
from bounded_contexts.team.models import Team
from bounded_contexts.user.models import User
from core.consts import DEMO_USER_EMAIL
from core.services.password import hash_password
from core.settings import FRIENDLY_CHAMPIONSHIP_NAME
from infra.database import get_session


def _populate() -> None:
    session = next(get_session())
    if session.exec(select(Team).where(Team.deleted == False)).first():
        print("Database already populated")
        return

    team1_id = uuid4()
    team1_mocks = [
        Team(
            id=team1_id,
            name="Demo FC",
            emblem_url="https://i.postimg.cc/2jKvC0WY/emblema-demo.png",
            foundation_date=date(2023, 1, 1),
            season_start_date=date(2023, 1, 1),
        ),
        User(
            team_id=team1_id,
            name="Usuário Demo",
            email=DEMO_USER_EMAIL,
            hashed_password=hash_password("gamalabs#demo"),
            is_admin=True,
        ),
        User(
            team_id=team1_id,
            name="José da Silva",
            email="josedasilva@demofc.com",
            hashed_password=hash_password("1234"),
        ),
        User(
            team_id=team1_id,
            name="Super User",
            email="superuser@demofc.com",
            hashed_password=hash_password("1234"),
            is_super_admin=True,
        ),
        Championship(
            team_id=team1_id,
            name=FRIENDLY_CHAMPIONSHIP_NAME,
            start_date=date(1800, 1, 1),
            is_league_format=True,
        ),
        Championship(
            team_id=team1_id,
            name="Champions League 2024",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
            is_league_format=False,
            final_stage=FinalStageOptions.SEMI_FINAL,
        ),
        Championship(
            team_id=team1_id,
            name="Brasileirão 2025",
            start_date=date(2025, 1, 1),
            is_league_format=True,
        ),
    ]

    team2_id = uuid4()
    team2_mocks = [
        Team(
            id=team2_id,
            name="Tribunata",
            foundation_date=date(1899, 11, 29),
            season_start_date=date(2023, 1, 1),
        ),
        User(
            team_id=team2_id,
            name="Gabriel Martins",
            email="gab@tribunata.com",
            hashed_password=hash_password("1234"),
            is_admin=True,
        ),
        User(
            team_id=team2_id,
            name="José da Silva",
            email="josedasilva@tribunata.com",
            hashed_password=hash_password("1234"),
        ),
        User(
            team_id=team2_id,
            name="Super User",
            email="superuser@tribunata.com",
            hashed_password=hash_password("1234"),
            is_super_admin=True,
        ),
        Championship(
            team_id=team2_id,
            name=FRIENDLY_CHAMPIONSHIP_NAME,
            start_date=date(1800, 1, 1),
            is_league_format=True,
        ),
        Championship(
            team_id=team2_id,
            name="Chuteira de Aço 2024",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
            is_league_format=False,
            final_stage=FinalStageOptions.CAMPEAO,
        ),
        Championship(
            team_id=team2_id,
            name="Chuteira de Aço 2025",
            start_date=date(2025, 4, 1),
            is_league_format=False,
        ),
    ]

    teams_mocks = [team1_mocks, team2_mocks]

    for team_mocks in teams_mocks:
        for mock in team_mocks:
            session.add(mock)
            if isinstance(mock, Team):
                session.flush()
    session.commit()
    session.close()


_populate()
