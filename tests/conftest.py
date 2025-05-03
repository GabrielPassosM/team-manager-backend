import pytest

from bounded_contexts.team.models import Team
from infra.database import get_session


@pytest.fixture(scope="function")
def mock_team():
    mock = Team(
        name="FC Barcelona",
        emblem_url="https://example.com/image.jpg",
        foundation_date="2023-01-01",
    )
    session = get_session()
    session.add(mock)
    session.commit()
    session.refresh(mock)
    yield mock
