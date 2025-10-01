from collections import defaultdict
from datetime import date, timedelta
from uuid import UUID

from bson import ObjectId
from fastapi import HTTPException
from sqlmodel import Session

from bounded_contexts.championship.repo import ChampionshipReadRepo
from bounded_contexts.championship.schemas import (
    ChampionshipCreate,
    ChampionshipResponse,
)
from bounded_contexts.championship.service import create_championship
from bounded_contexts.team.exceptions import TeamNotFound
from bounded_contexts.team.repo import (
    TeamWriteRepo,
    IntentionToSubscribeReadRepo,
    IntentionToSubscribeWriteRepo,
    TeamReadRepo,
)
from bounded_contexts.team.schemas import (
    TeamRegister,
    TeamCreate,
    RegisterTeamResponse,
    RenewSubscriptionIn,
    RenewSubscriptionResponse,
    CurrentTeamResponse,
)
from bounded_contexts.user.models import User
from bounded_contexts.user.repo import UserReadRepo
from bounded_contexts.user.schemas import UserCreate, UserResponse
from bounded_contexts.user.service import create_user
from core.settings import (
    FRIENDLY_CHAMPIONSHIP_NAME,
    SUPER_USER_PWD,
    BEFORE_SYSTEM_CHAMPIONSHIP_NAME,
)
from libs.datetime import add_or_subtract_months_to_date, brasilia_now


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

    # 4 - Create default championships (friendly and before system)
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

    before_system_championship = ChampionshipReadRepo(session).get_by_name(
        BEFORE_SYSTEM_CHAMPIONSHIP_NAME, team_created.id
    )
    if not before_system_championship:
        before_system_championship = create_championship(
            create_data=ChampionshipCreate(
                name=BEFORE_SYSTEM_CHAMPIONSHIP_NAME,
                start_date=date(1800, 1, 1),
                end_date=(brasilia_now() - timedelta(days=1)).date(),
                is_league_format=True,
            ),
            current_user=super_user,
            session=session,
        )

    IntentionToSubscribeWriteRepo(session).delete(intention_data)

    return RegisterTeamResponse(
        team=CurrentTeamResponse.model_validate(team_created),
        super_user=UserResponse.model_validate(super_user),
        client_user=UserResponse.model_validate(client_user),
        friendly_championship=ChampionshipResponse.model_validate(
            friendly_championship
        ),
        before_system_championship=ChampionshipResponse.model_validate(
            before_system_championship
        ),
    )


def _generate_super_user_email(team_name: str) -> str:
    return f"superuser@{team_name[:30].lower().replace(" ", "")}.com"


def renew_teams_subscription(
    renew_data: RenewSubscriptionIn, session: Session, current_user_id: UUID
) -> RenewSubscriptionResponse:
    teams = TeamReadRepo(session).get_by_ids(renew_data.team_ids)
    if not teams or len(teams) != len(renew_data.team_ids):
        raise TeamNotFound()

    renewed_info = defaultdict(list)
    for team in teams:
        new_paid_until = add_or_subtract_months_to_date(
            team.paid_until, renew_data.months
        )
        team.paid_until = new_paid_until
        TeamWriteRepo(session).save_without_commit(
            team, current_user_id=current_user_id
        )
        renewed_info[new_paid_until].append(team.name)
    session.commit()

    return RenewSubscriptionResponse(renewed_info=renewed_info)
