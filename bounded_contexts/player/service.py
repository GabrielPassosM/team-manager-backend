from uuid import UUID

from sqlmodel import Session

from bounded_contexts.player.models import Player
from bounded_contexts.player.repo import PlayerReadRepo, PlayerWriteRepo
from bounded_contexts.player.schemas import PlayerCreate
from bounded_contexts.team.exceptions import TeamNotFound
from bounded_contexts.team.repo import TeamReadRepo
from bounded_contexts.user.models import User


def create_player(
    create_data: PlayerCreate, current_user: User, session: Session
) -> Player:
    if not TeamReadRepo(session=session).get_by_id(current_user.team_id):
        raise TeamNotFound()

    return PlayerWriteRepo(session=session).save(
        create_data, current_user.team_id, current_user.id
    )


def get_players_by_team(team_id: UUID, session: Session) -> list[Player]:
    return PlayerReadRepo(session=session).get_all(team_id)
