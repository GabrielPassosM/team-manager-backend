from uuid import UUID
from zoneinfo import ZoneInfo

from sqlmodel import Session

from bounded_contexts.championship.exceptions import ChampionshipNotFound
from bounded_contexts.championship.repo import ChampionshipReadRepo
from bounded_contexts.game_and_stats.exceptions import (
    GameDateOutsideChampionshipRange,
    InvalidChampionshipFormat,
)
from bounded_contexts.game_and_stats.game.repo import GameWriteRepo, GameReadRepo
from bounded_contexts.game_and_stats.game.schemas import (
    GameCreate,
    GameResponse,
    GamesPageResponse,
)
from bounded_contexts.game_and_stats.stats.service import create_game_stats
from bounded_contexts.team.exceptions import TeamNotFound
from bounded_contexts.team.repo import TeamReadRepo
from bounded_contexts.user.models import User
from core.exceptions import AdminRequired


def create_game_and_stats(
    create_data: GameCreate, current_user: User, session: Session
) -> UUID:
    if not current_user.has_admin_privileges:
        raise AdminRequired()
    if not TeamReadRepo(session=session).get_by_id(current_user.team_id):
        raise TeamNotFound()

    championship = ChampionshipReadRepo(session).get_by_id(create_data.championship_id)
    if not championship:
        raise ChampionshipNotFound()
    if (championship.is_league_format and create_data.stage) or (
        not championship.is_league_format and create_data.round
    ):
        raise InvalidChampionshipFormat()

    # TODO add timezone config in Team
    create_data.date_hour = create_data.date_hour.replace(
        tzinfo=ZoneInfo("America/Sao_Paulo")
    )
    game_date = create_data.date_hour.date()
    if not championship.date_is_within_championship(game_date):
        raise GameDateOutsideChampionshipRange(champ_date_range=championship.date_range)

    game = GameWriteRepo(session).create_without_commit(
        create_data, current_user.team_id, current_user.id
    )

    create_game_stats(create_data, game.id, current_user, session)

    session.commit()
    return game.id


def get_games_paginated(
    team_id: UUID, limit: int, offset: int, session: Session
) -> GamesPageResponse:
    games = GameReadRepo(session).get_all_paginated(team_id, limit, offset)

    response_items = []
    for game in games:
        response = GameResponse(
            id=game.id,
            championship_name=game.championship.name[:40],
            adversary=game.adversary[:30],
            date_hour=game.date_hour,
            round=game.round,
            stage=game.stage,
            is_home=game.is_home,
            is_wo=game.is_wo,
            team_score=game.team_score,
            adversary_score=game.adversary_score,
            team_penalty_score=game.team_penalty_score,
            adversary_penalty_score=game.adversary_penalty_score,
        )
        response_items.append(response)

    total = GameReadRepo(session).count_all(team_id)
    return GamesPageResponse(
        items=response_items, total=total, limit=limit, offset=offset
    )
