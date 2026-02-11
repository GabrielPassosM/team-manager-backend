from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session

from bounded_contexts.championship.repo import ChampionshipWriteRepo
from bounded_contexts.championship.schemas import ChampionshipCreate
from bounded_contexts.championship.service import create_championship
from bounded_contexts.game_and_stats.availability.repo import AvailabilityWriteRepo
from bounded_contexts.game_and_stats.game.repo import GameWriteRepo
from bounded_contexts.game_and_stats.game.schemas import (
    GameCreate,
    GoalAndAssist,
    PlayerAndQuantity,
)
from bounded_contexts.game_and_stats.game.service import create_game_and_stats
from bounded_contexts.game_and_stats.stats.repo import GamePlayerStatWriteRepo
from bounded_contexts.player.models import PlayerPositions
from bounded_contexts.player.repo import PlayerWriteRepo
from bounded_contexts.player.schemas import PlayerCreate
from bounded_contexts.team.repo import TeamReadRepo, TeamWriteRepo
from bounded_contexts.team.schemas import TeamUpdate
from bounded_contexts.user.repo import UserReadRepo, UserWriteRepo
from bounded_contexts.storage.service import delete_all_players_images
from core.consts import DEMO_USER_EMAIL, DEFAULT_PRIMARY_COLOR
from core.settings import FRIENDLY_CHAMPIONSHIP_NAME, BEFORE_SYSTEM_CHAMPIONSHIP_NAME
from infra.database import get_session
from libs.datetime import utcnow, brasilia_now

router = APIRouter(prefix="/cron", tags=["Cronjobs"])


@router.get("/reset-demo-team-data")
def reset_demo_team_data(session: Session = Depends(get_session)):
    now = utcnow()
    if now.hour < 6 or now.hour > 7:
        return JSONResponse({"message": "Not allowed"}, status_code=403)

    # 1 - Delete all data related to the demo team, except the super user and the demo user
    user_read_repo = UserReadRepo(session)
    admin_demo_user = user_read_repo.get_by_email(DEMO_USER_EMAIL)
    if not admin_demo_user:
        raise HTTPException(status_code=404, detail="Demo user not found")

    team_id = admin_demo_user.team_id

    AvailabilityWriteRepo(session).hard_delete_all_by_team_id(team_id)
    GamePlayerStatWriteRepo(session).hard_delete_all_by_team_id(team_id)
    GameWriteRepo(session).hard_delete_all_by_team_id(team_id)
    ChampionshipWriteRepo(session).hard_delete_all_by_team_id(team_id)
    PlayerWriteRepo(session).hard_delete_all_by_team_id(team_id)
    delete_all_players_images(str(team_id))

    user_write_repo = UserWriteRepo(session)
    super_user = user_read_repo.get_team_super_user(team_id)
    user_ids = user_read_repo.get_ids_by_team_id(team_id)
    user_ids.remove(super_user.id)
    user_ids.remove(admin_demo_user.id)

    user_write_repo.hard_delete_logged_users_by_user_ids(user_ids)
    user_write_repo.hard_delete_by_user_ids(user_ids)

    # 2 - Recreate base data
    friendly_championship = create_championship(
        create_data=ChampionshipCreate(
            name=FRIENDLY_CHAMPIONSHIP_NAME,
            start_date=date(1800, 1, 1),
            is_league_format=True,
        ),
        current_user=super_user,
        session=session,
    )
    create_championship(
        create_data=ChampionshipCreate(
            name=BEFORE_SYSTEM_CHAMPIONSHIP_NAME,
            start_date=date(1800, 1, 1),
            end_date=(brasilia_now() - timedelta(days=1)).date(),
            is_league_format=True,
        ),
        current_user=super_user,
        session=session,
    )

    player1 = PlayerWriteRepo(session=session).create(
        PlayerCreate(name="Cláudio", shirt_number=7, position=PlayerPositions.PONTA),
        team_id,
        super_user.id,
    )
    player2 = PlayerWriteRepo(session=session).create(
        PlayerCreate(
            name="Danilo", shirt_number=8, position=PlayerPositions.MEIO_CAMPO
        ),
        team_id,
        super_user.id,
    )

    game_data = GameCreate(
        championship_id=friendly_championship.id,
        adversary="Outro Time FC",
        date_hour=brasilia_now() - timedelta(hours=12),
        team_score=2,
        adversary_score=1,
        players=[player1.id, player2.id],
        goals_and_assists=[
            GoalAndAssist(goal_player_id=player1.id, assist_player_id=player2.id),
            GoalAndAssist(goal_player_id=player2.id, assist_player_id=None),
        ],
        yellow_cards=[PlayerAndQuantity(player_id=player1.id, quantity=1)],
        mvps=[
            PlayerAndQuantity(player_id=player1.id, quantity=2),
            PlayerAndQuantity(player_id=player2.id, quantity=3),
        ],
    )

    create_game_and_stats(
        create_data=game_data,
        current_user=super_user,
        session=session,
    )

    team = TeamReadRepo(session=session).get_by_id(team_id)
    TeamWriteRepo(session=session).update(
        team,
        TeamUpdate(
            name=team.name,
            emblem_url=team.emblem_url,
            foundation_date=date(2018, 11, 15),
            season_start_date=date(brasilia_now().year, 1, 1),
            season_end_date=None,
            primary_color=DEFAULT_PRIMARY_COLOR,
        ),
        super_user.id,
    )

    return JSONResponse({"message": "Demo team data reset successfully"})
