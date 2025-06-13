from bounded_contexts.team.exceptions import TeamNotFound
from bounded_contexts.team.models import Team
from bounded_contexts.team.repo import TeamWriteRepo, TeamReadRepo
from bounded_contexts.team.schemas import TeamCreate, TeamUpdate

from uuid import UUID
from sqlmodel import Session

from bounded_contexts.user.models import User


def create_team(team_data: TeamCreate, session: Session) -> Team:
    return TeamWriteRepo(session=session).create(team_data)


def get_team_by_id(team_id: UUID, session: Session) -> Team:
    team = TeamReadRepo(session=session).get_by_id(team_id)
    if not team:
        raise TeamNotFound()

    return team


def update_team(current_user: User, team_data: TeamUpdate, session: Session) -> Team:
    team = TeamReadRepo(session=session).get_by_id(current_user.team_id)
    if not team:
        raise TeamNotFound()

    if all(
        [
            team.name == team_data.name,
            team.emblem_url == team_data.emblem_url,
            team.foundation_date == team_data.foundation_date,
            team.season_start_date == team_data.season_start_date,
            team.season_end_date == team_data.season_end_date,
            team.primary_color == team_data.primary_color,
        ]
    ):
        return team

    updated_team = TeamWriteRepo(session=session).update(
        team, team_data, current_user.id
    )

    return updated_team


def delete_team(team_id: UUID, session: Session) -> None:
    team = TeamReadRepo(session=session).get_by_id(team_id)
    if not team:
        raise TeamNotFound

    TeamWriteRepo(session=session).delete(team)
