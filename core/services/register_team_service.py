from datetime import date
from uuid import UUID

from bson import ObjectId
from fastapi import HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from bounded_contexts.championship.repo import ChampionshipReadRepo
from bounded_contexts.championship.schemas import ChampionshipCreate
from bounded_contexts.championship.service import create_championship
from bounded_contexts.team.repo import TeamWriteRepo, IntentionToSubscribeReadRepo
from bounded_contexts.team.schemas import TeamRegister, TeamCreate
from bounded_contexts.user.models import User
from bounded_contexts.user.repo import UserReadRepo
from bounded_contexts.user.schemas import UserCreate
from bounded_contexts.user.service import create_user
from core.settings import FRIENDLY_CHAMPIONSHIP_NAME, SUPER_USER_PWD


class RegisterTeamResponse(BaseModel):
    team: UUID
    super_user_email: str
    client_user_email: str
    friendly_championship: UUID


def register_new_team_and_create_base_models(
    register_data: TeamRegister, session: Session
) -> RegisterTeamResponse:
    # 1 - Create the team
    intention_data = IntentionToSubscribeReadRepo(session).get_by_email(
        register_data.user_email
    )
    if not intention_data:
        raise HTTPException(
            status_code=400,
            detail="No intention to subscribe found for this email.",
        )

    team_created = TeamWriteRepo(session=session).create(
        TeamCreate(name=intention_data.team_name)
    )

    if not team_created:
        raise HTTPException(status_code=500, detail="Team could not be created.")

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
                email=_generate_super_user_email(team_created.name),
                password=SUPER_USER_PWD,
                is_admin=False,
                is_super_admin=True,
            ),
            current_user=fake_current_user,
            session=session,
        )

    # 3 - Create first client user
    client_user = UserReadRepo(session=session).get_by_email(intention_data.user_email)
    if client_user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )
    client_user = create_user(
        user_data=UserCreate(
            name=intention_data.user_name,
            email=intention_data.user_email,
            password=str(ObjectId()),
            is_admin=True,
            is_super_admin=False,
        ),
        current_user=super_user,
        session=session,
    )

    # 4 - Create Friendly championship
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
            current_user=super_user,
            session=session,
        )

    return RegisterTeamResponse(
        team=team_created.id,
        super_user_email=super_user.email,
        client_user_email=client_user.email,
        friendly_championship=friendly_championship.id,
    )


def _generate_super_user_email(team_name: str) -> str:
    return team_name[:30].lower().replace(" ", "") + "@superuser.com"
