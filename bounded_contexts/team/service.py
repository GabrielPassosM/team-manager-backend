from bounded_contexts.team.exceptions import TeamNotFound
from bounded_contexts.team.models import Team
from bounded_contexts.team.repo import TeamWriteRepo, TeamReadRepo
from bounded_contexts.team.schemas import TeamCreate
from libs.base_types.uuid import BaseUUID


def create_team(team_data: TeamCreate) -> Team:
    return TeamWriteRepo().save(team_data)


def get_team_by_id(team_id: BaseUUID) -> Team:
    team = TeamReadRepo().get_by_id(team_id)
    if not team:
        raise TeamNotFound()

    return team


def delete_team(team_id: BaseUUID) -> None:
    team = TeamReadRepo().get_by_id(team_id)
    if not team:
        raise TeamNotFound

    TeamWriteRepo().delete(team)
