from uuid import UUID

from sqlmodel import Session

from bounded_contexts.championship.exceptions import ChampionshipNotFound
from bounded_contexts.championship.repo import ChampionshipReadRepo
from bounded_contexts.game_and_stats.availability.service import (
    delete_game_players_availability,
)
from bounded_contexts.game_and_stats.exceptions import (
    GameDateOutsideChampionshipRange,
    InvalidChampionshipFormat,
    GameNotFound,
)
from bounded_contexts.game_and_stats.game.repo import GameWriteRepo, GameReadRepo
from bounded_contexts.game_and_stats.game.schemas import (
    GameCreate,
    GameResponse,
    GamesPageResponse,
    GameUpdate,
    GameInfoIn,
    GameStatsIn,
    NameAndId,
    GameAndStatsToUpdateResponse,
    GoalAndAssist,
    PlayerAndQuantity,
    GameFilter,
)
from bounded_contexts.game_and_stats.models import Game, StatOptions
from bounded_contexts.game_and_stats.stats.repo import GamePlayerStatReadRepo
from bounded_contexts.game_and_stats.stats.service import (
    create_game_stats,
    update_game_stats,
    delete_game_stats,
    reactivate_game_stats,
)
from bounded_contexts.team.exceptions import TeamNotFound
from bounded_contexts.team.repo import TeamReadRepo
from bounded_contexts.user.models import User
from core.exceptions import AdminRequired, SuperAdminRequired


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

    game_date = create_data.date_hour.date()
    if not championship.date_is_within_championship(game_date):
        raise GameDateOutsideChampionshipRange(champ_date_range=championship.date_range)

    game = GameWriteRepo(session).create_without_commit(
        create_data, current_user.team_id, current_user.id
    )

    stats_data = GameStatsIn(**create_data.model_dump())
    create_game_stats(stats_data, game.id, current_user, session)

    session.commit()
    return game.id


def get_game_and_stats_to_update(
    game_id: UUID, session: Session
) -> GameAndStatsToUpdateResponse:
    game = GameReadRepo(session).get_by_id(game_id)
    if not game:
        raise GameNotFound()

    game_stats = GamePlayerStatReadRepo(session).get_by_game_id(game_id)

    assists_lookup = {
        s.related_stat_id: s for s in game_stats if s.stat == StatOptions.ASSIST
    }

    players = []
    goals_and_assists = []
    yellow_cards = []
    red_cards = []
    mvps = []
    for stat in game_stats:
        player = stat.player

        if stat.stat == StatOptions.PLAYED:
            players.append(player.id)
        elif stat.stat == StatOptions.GOAL:
            assist = assists_lookup.get(stat.id)
            goal_player_id = player.id if player else None
            assist_player_id = assist.player.id if assist else None
            goals_and_assists.append(
                GoalAndAssist(
                    goal_player_id=goal_player_id,
                    assist_player_id=assist_player_id,
                )
            )
        elif stat.stat == StatOptions.YELLOW_CARD:
            yellow_cards.append(
                PlayerAndQuantity(
                    player_id=player.id,
                    quantity=stat.quantity,
                )
            )
        elif stat.stat == StatOptions.RED_CARD:
            red_cards.append(player.id)
        elif stat.stat == StatOptions.MVP:
            mvps.append(
                PlayerAndQuantity(
                    player_id=player.id,
                    quantity=stat.quantity,
                )
            )

    champ = game.championship

    return GameAndStatsToUpdateResponse(
        id=game.id,
        championship=NameAndId(id=champ.id, name=champ.name[:40]),
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
        players=players,
        goals_and_assists=goals_and_assists,
        yellow_cards=yellow_cards,
        red_cards=red_cards,
        mvps=mvps,
    )


def get_games_filtered_and_paginated(
    team_id: UUID, filter_data: GameFilter, limit: int, offset: int, session: Session
) -> GamesPageResponse:
    if filter_data.is_empty:
        games, total_games = GameReadRepo(session).get_all_paginated(
            team_id, limit, offset
        )
    else:
        games, total_games = GameReadRepo(session).get_by_filters_paginated(
            team_id, filter_data, limit, offset
        )

    response_items = []
    for game in games:
        response = GameResponse(
            id=game.id,
            championship=NameAndId(
                id=game.championship_id, name=game.championship.name[:40]
            ),
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

    return GamesPageResponse(
        items=response_items, total=total_games, limit=limit, offset=offset
    )


def update_game_and_stats(
    game_id: UUID, update_data: GameUpdate, current_user: User, session: Session
):
    if not current_user.has_admin_privileges:
        raise AdminRequired()

    game = GameReadRepo(session).get_by_id(game_id)
    if not game:
        raise GameNotFound()

    update_game_data = GameInfoIn(**update_data.model_dump())
    update_stats_data = GameStatsIn(**update_data.model_dump())

    has_game_update = _verify_game_changes(game, update_game_data)

    if not has_game_update and not update_data.has_stats_update:
        return

    if has_game_update:
        _validate_game_update_request(update_game_data, session)

        GameWriteRepo(session).update_without_commit(
            game, update_game_data, current_user.id
        )

    if update_data.has_stats_update:
        update_game_stats(update_stats_data, game_id, current_user, session)

    session.commit()


def _verify_game_changes(game: Game, update_game_data: GameInfoIn) -> bool:
    game_data = game.model_dump()
    update_game_data = update_game_data.model_dump()

    has_game_update = False
    for key, value in update_game_data.items():
        if game_data[key] != value:
            has_game_update = True
            break
    return has_game_update


def _validate_game_update_request(update_data: GameInfoIn, session: Session) -> None:
    championship = ChampionshipReadRepo(session).get_by_id(update_data.championship_id)
    if not championship:
        raise ChampionshipNotFound()

    if (championship.is_league_format and update_data.stage) or (
        not championship.is_league_format and update_data.round
    ):
        raise InvalidChampionshipFormat()

    game_date = update_data.date_hour.date()
    if not championship.date_is_within_championship(game_date):
        raise GameDateOutsideChampionshipRange(champ_date_range=championship.date_range)


def delete_game_and_dependent_tables(
    game_id: UUID, current_user: User, session: Session
) -> None:
    if not current_user.has_admin_privileges:
        raise AdminRequired()

    game = GameReadRepo(session).get_by_id(game_id)
    if not game:
        raise GameNotFound()

    current_user_id = current_user.id
    try:
        GameWriteRepo(session).delete_without_commit(game, current_user_id)
        delete_game_stats(game_id, current_user_id, session)
        delete_game_players_availability(game_id, current_user_id, session)
    except Exception as e:
        session.rollback()
        raise e

    session.commit()


def reactivate_game_and_stats(
    game_id: UUID, current_user: User, session: Session
) -> None:
    if not current_user.is_super_admin:
        raise SuperAdminRequired()

    game = GameReadRepo(session).get_by_id(game_id, deleted=True)
    if not game:
        raise GameNotFound()

    current_user_id = current_user.id
    try:
        GameWriteRepo(session).reactivate_without_commit(game, current_user_id)
        reactivate_game_stats(game_id, current_user_id, session)
    except Exception as e:
        session.rollback()
        raise e

    session.commit()
