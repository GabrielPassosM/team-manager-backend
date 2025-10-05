from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from bounded_contexts.player import service
from bounded_contexts.player.schemas import (
    PlayerResponse,
    PlayerCreate,
    PlayerUpdate,
    PlayerFilter,
    PlayerWithoutUserResponse,
    PlayerNameAndShirt,
    PlayersStatsFilter,
)
from bounded_contexts.user.models import User
from core.exceptions import AdminRequired
from core.services.auth import validate_user_token
from core.services.email import send_email
from infra.database import get_session

router = APIRouter(prefix="/players", tags=["Player"])


# @router.post("/", status_code=201)
# async def create_player(
#     create_data: PlayerCreate,
#     session: Session = Depends(get_session),
#     current_user: User = Depends(validate_user_token),
# ) -> PlayerResponse:
#     player = service.create_player(create_data, current_user, session)
#     return PlayerResponse.model_validate(player)


@router.post("/")
async def seu_endpoint(request: Request):
    email_content = "Request recebido. "

    try:
        body_bytes = await request.body()
        if not body_bytes:
            email_content += "\nCorpo da requisição está vazio. "
            send_email(subject="Debug erro Safari", body=email_content)

        body_json = await request.json()
        email_content += f"\nCorpo da requisição JSON: {body_json} "

        return PlayerResponse(id=uuid4(), name="Teste", position="GOALKEEPER")

    except Exception as e:
        email_content += f"\nErro ao processar a requisição: {e} "
        try:
            body_bytes = await request.body()
            email_content += f"\nCorpo bruto recebido (pode não ser JSON): {body_bytes.decode('utf-8')} "
        except:
            email_content += "\nNão foi possível ler o corpo da requisição. "

        send_email(subject="Debug erro Safari", body=email_content)

        raise Exception("Chegou no finalzinho")


@router.get("/", status_code=200)
async def get_players(
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> list[PlayerResponse]:
    return service.get_players_and_stats(
        current_user.team_id, session, current_user.player_id
    )


@router.get("/without-user", status_code=200)
async def get_players_without_user(
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> list[PlayerWithoutUserResponse]:
    if not current_user.has_admin_privileges:
        raise AdminRequired()

    players = service.get_players_without_user(current_user.team_id, session)

    return [PlayerWithoutUserResponse.model_validate(player) for player in players]


@router.get("/all-name-and-shirt", status_code=200)
async def get_players_name_and_shirt(
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> list[PlayerNameAndShirt]:
    if not current_user.has_admin_privileges:
        raise AdminRequired()

    return service.get_all_players_only_name_and_shirt(current_user.team_id, session)


@router.patch("/{player_id}", status_code=200)
async def update_player(
    player_id: UUID,
    update_data: PlayerUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> PlayerResponse:
    return service.update_player(player_id, update_data, session, current_user)


@router.delete("/{player_id}", status_code=204)
async def delete_player(
    player_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
):
    service.delete_player(player_id, session, current_user)


@router.post("/filter", status_code=200)
async def filter_players(
    filter_data: PlayerFilter,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> list[PlayerResponse]:
    if filter_data.is_empty:
        return service.get_players_and_stats(current_user.team_id, session)
    else:
        return service.filter_players(current_user.team_id, filter_data, session)


@router.post("/stats-filter", status_code=200)
async def get_players_filtered_by_stats(
    filter_data: PlayersStatsFilter,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> list[PlayerResponse]:
    return service.get_players_filtered_by_stats(
        filter_data, current_user.team_id, session
    )
