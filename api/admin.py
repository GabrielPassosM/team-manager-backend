from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

import core.services.admin_service as service
from bounded_contexts.team.schemas import (
    TeamRegister,
    RenewSubscriptionIn,
    RegisterTeamResponse,
    RenewSubscriptionResponse,
)
from bounded_contexts.user.models import User
from core.exceptions import SuperAdminRequired
from core.services import migrations_service
from core.services.auth import validate_user_token
from core.settings import MIGRATIONS_PWD
from infra.database import get_session

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/run-migrations/{password}", status_code=200)
async def run_migrations(password: str):
    return migrations_service.run_migrations(password)


@router.get("/pending-migrations")
async def check_pending_migrations():
    return migrations_service.get_pending_migrations()


@router.post("/register-team/{password}", status_code=201)
async def register_new_team(
    password: str,
    register_data: TeamRegister,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> RegisterTeamResponse:
    if not current_user.is_super_admin:
        raise SuperAdminRequired()

    # TODO rename MIGRATIONS_PWD to ADMIN_PWD
    if password != MIGRATIONS_PWD:
        raise HTTPException(status_code=401, detail="Invalid password")

    return service.register_new_team_and_create_base_models(register_data, session)


@router.post("/renew-subscription", status_code=200)
async def renew_subscription(
    renew_data: RenewSubscriptionIn,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> RenewSubscriptionResponse:
    if not current_user.is_super_admin:
        raise SuperAdminRequired()

    return service.renew_teams_subscription(renew_data, session, current_user.id)
