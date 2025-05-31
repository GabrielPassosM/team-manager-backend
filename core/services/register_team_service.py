from datetime import date
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from bounded_contexts.championship.repo import ChampionshipReadRepo
from bounded_contexts.championship.schemas import ChampionshipCreate
from bounded_contexts.championship.service import create_championship
from bounded_contexts.team.repo import TeamWriteRepo, TeamReadRepo
from bounded_contexts.team.schemas import TeamRegister, TeamCreate
from bounded_contexts.user.models import User
from bounded_contexts.user.repo import UserReadRepo
from bounded_contexts.user.schemas import UserCreate
from bounded_contexts.user.service import create_user
from core.settings import FRIENDLY_CHAMPIONSHIP_NAME


class RegisterTeamResponse(BaseModel):
    team: UUID
    super_user: UUID
    friendly_championship: UUID


def register_new_team_and_create_base_models(
    register_data: TeamRegister, session: Session
) -> RegisterTeamResponse:
    # 1 - Create the team
    if register_data.team_id:
        team_created = TeamReadRepo(session).get_by_id(register_data.team_id)
    else:
        team_data = TeamCreate(
            name=register_data.name,
            emblem_url=register_data.emblem_url,
            foundation_date=register_data.foundation_date,
            season_start_date=register_data.season_start_date,
            season_end_date=register_data.season_end_date,
            primary_color=register_data.primary_color,
            paid_until=register_data.paid_until,
        )
        team_created = TeamWriteRepo(session=session).save(team_data)

    if not team_created:
        raise HTTPException(
            status_code=400, detail="Team could not be created or found."
        )

    fake_current_user = User(
        id=None,  # so dont save the created_by
        team_id=team_created.id,  # the services functions use this attribute
        name="Fake User",
        email="fakeemail@gmail.com",
        is_super_admin=True,
    )

    # 2 - Create the super admin user
    super_user = UserReadRepo(session=session).get_team_super_user(team_created.id)
    if not super_user:
        super_user = create_user(
            user_data=UserCreate(
                name="Super User",
                email=register_data.user_email,
                password=register_data.user_password,
                is_admin=False,
                is_super_admin=True,
            ),
            current_user=fake_current_user,
            session=session,
        )

    # 3 - Create Friendly championship
    friendly_championship = ChampionshipReadRepo(session).get_by_name(
        FRIENDLY_CHAMPIONSHIP_NAME, team_created.id
    )
    if not friendly_championship:
        friendly_championship = create_championship(
            create_data=ChampionshipCreate(
                name=FRIENDLY_CHAMPIONSHIP_NAME,
                start_date=date(1800, 1, 1),
                is_league_format=True,
            ),
            current_user=fake_current_user,
            session=session,
        )

    return RegisterTeamResponse(
        team=team_created.id,
        super_user=super_user.id,
        friendly_championship=friendly_championship.id,
    )
