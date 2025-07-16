from uuid import UUID

from sqlmodel import Session

from bounded_contexts.game_and_stats.exceptions import SomePlayersNotFound, GameNotFound
from bounded_contexts.game_and_stats.game.repo import GameReadRepo
from bounded_contexts.game_and_stats.game.schemas import GameStatsIn
from bounded_contexts.game_and_stats.models import StatOptions
from bounded_contexts.game_and_stats.stats.repo import (
    GamePlayerStatReadRepo,
    GamePlayerStatWriteRepo,
)
from bounded_contexts.game_and_stats.stats.schemas import (
    GameStatsResponse,
    MonthTopScorerResponse,
)
from bounded_contexts.player.repo import PlayerReadRepo
from bounded_contexts.user.models import User


def create_game_stats(
    create_data: GameStatsIn, game_id: UUID, current_user: User, session: Session
) -> None:
    if not create_data.players:
        return

    game_players = PlayerReadRepo(session).get_by_ids(create_data.players)
    game_players_ids = [p.id for p in game_players]
    if len(game_players) != len(create_data.players):
        raise SomePlayersNotFound()

    team_id = current_user.team_id
    current_user_id = current_user.id

    GamePlayerStatWriteRepo(session).create_single_quantity_stats_without_commit(
        StatOptions.PLAYED, team_id, game_id, game_players_ids, current_user_id
    )

    if create_data.goals_and_assists:
        GamePlayerStatWriteRepo(session).create_goals_and_assists_without_commit(
            team_id,
            game_id,
            create_data.goals_and_assists,
            game_players_ids,
            current_user_id,
        )

    if create_data.yellow_cards:
        GamePlayerStatWriteRepo(
            session
        ).create_stats_per_player_quantity_without_commit(
            StatOptions.YELLOW_CARD,
            team_id,
            game_id,
            create_data.yellow_cards,
            game_players_ids,
            current_user_id,
        )

    if create_data.red_cards:
        GamePlayerStatWriteRepo(session).create_single_quantity_stats_without_commit(
            StatOptions.RED_CARD,
            team_id,
            game_id,
            create_data.red_cards,
            current_user_id,
            game_players_ids,
        )

    if create_data.mvps:
        GamePlayerStatWriteRepo(
            session
        ).create_stats_per_player_quantity_without_commit(
            StatOptions.MVP,
            team_id,
            game_id,
            create_data.mvps,
            game_players_ids,
            current_user_id,
        )


def get_game_stats(game_id: UUID, session: Session) -> GameStatsResponse:
    if not GameReadRepo(session).get_by_id(game_id):
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
        player_name = stat.player.name if stat.player else "Contra"

        if stat.stat == StatOptions.GOAL:
            assist = assists_lookup.get(stat.id)
            assist_name = assist.player.name if assist else None

            goals_and_assists.append(
                {"player_name": player_name, "assist_player_name": assist_name}
            )
        elif stat.stat == StatOptions.YELLOW_CARD:
            yellow_cards.append([player_name, stat.quantity])
        elif stat.stat == StatOptions.RED_CARD:
            red_cards.append(player_name)
        elif stat.stat == StatOptions.MVP:
            mvps.append([player_name, stat.quantity])
        elif stat.stat == StatOptions.PLAYED:
            shirt_number = stat.player.shirt_number
            position = stat.player.position
            players.append([position, shirt_number, player_name])

    mvps = sorted(mvps, key=lambda item: item[1], reverse=True)
    players = sorted(players, key=lambda item: item[1])

    return GameStatsResponse(
        players=players,
        goals_and_assists=goals_and_assists,
        yellow_cards=yellow_cards,
        red_cards=red_cards,
        mvps=mvps,
    )


def update_game_stats(
    update_data: GameStatsIn, game_id: UUID, current_user: User, session: Session
) -> None:
    try:
        GamePlayerStatWriteRepo(session).hard_delete_without_commit_by_game_id(game_id)
        create_game_stats(update_data, game_id, current_user, session)
    except Exception as e:
        session.rollback()
        raise e


def delete_game_stats(game_id: UUID, current_user_id: UUID, session: Session) -> None:
    stats = GamePlayerStatReadRepo(session).get_by_game_id(game_id)
    if not stats:
        return

    GamePlayerStatWriteRepo(session).soft_delete_without_commit(stats, current_user_id)


def delete_player_stats(
    player_id: UUID, current_user_id: UUID, session: Session
) -> None:
    stats = GamePlayerStatReadRepo(session).get_by_player(player_id)
    if not stats:
        return

    GamePlayerStatWriteRepo(session).soft_delete_without_commit(stats, current_user_id)


def reactivate_game_stats(
    game_id: UUID, current_user_id: UUID, session: Session
) -> None:
    stats = GamePlayerStatReadRepo(session).get_by_game_id(game_id)
    if not stats:
        return

    GamePlayerStatWriteRepo(session).reactivate_without_commit(stats, current_user_id)


def get_month_top_scorer(
    team_id: UUID, session: Session
) -> MonthTopScorerResponse | None:
    player, goals, games = GamePlayerStatReadRepo(session).get_month_top_scorer(team_id)
    if not player:
        return None

    return MonthTopScorerResponse(
        id=player.id,
        name=player.name,
        image_url=player.image_url,
        shirt=player.shirt_number,
        goals=goals,
        games_played=games,
    )
