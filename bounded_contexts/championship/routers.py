from fastapi import APIRouter, Depends
from sqlmodel import Session

from bounded_contexts.championship import service
from bounded_contexts.championship.schemas import (
    ChampionshipCreate,
    ChampionshipResponse,
)
from bounded_contexts.user.models import User
from core.exceptions import AdminRequired
from core.services.auth import validate_user_token
from infra.database import get_session

router = APIRouter(prefix="/championships", tags=["Championship"])


@router.post("/", status_code=201)
async def create_championship(
    create_data: ChampionshipCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> ChampionshipResponse:
    if not current_user.has_admin_privileges:
        raise AdminRequired()

    championship = service.create_championship(
        create_data, current_user.team_id, session, current_user
    )
    return ChampionshipResponse.model_validate(championship)


@router.get("/", status_code=200)
async def get_championships(
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> list[ChampionshipResponse]:
    championships = service.get_championships_by_team(current_user.team_id, session)

    return [ChampionshipResponse.model_validate(champ) for champ in championships]
