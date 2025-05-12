from datetime import date
from uuid import uuid4

from sqlmodel import select

from bounded_contexts.team.models import Team
from bounded_contexts.user.models import User
from core.services.password import hash_password
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
            name="Time Demo",
            emblem_url="https://i.postimg.cc/2jKvC0WY/emblema-demo.png",
            foundation_date=date(2023, 1, 1),
        ),
        User(
            team_id=team1_id,
            name="Usuário Demo",
            email="usuariodemo@gamalabs.com",
            hashed_password=hash_password("gamalabs#demo"),
            is_admin=True,
        ),
    ]

    team2_id = uuid4()
    team2_mocks = [
        Team(
            id=team2_id,
            name="Tribunata",
            foundation_date=date(1899, 11, 29),
        ),
        User(
            team_id=team2_id,
            name="Gabriel Martins",
            email="gab@tribunata.com",
            hashed_password=hash_password("1234"),
            is_admin=True,
        ),
    ]

    teams_mocks = [team1_mocks, team2_mocks]

    for team_mocks in teams_mocks:
        for mock in team_mocks:
            session.add(mock)
    session.commit()


_populate()
