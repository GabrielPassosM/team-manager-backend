import pytest

from core.services.register_team_service import _generate_super_user_email


@pytest.mark.parametrize(
    "team_name, expected_email",
    [
        ("TeamA", "teama@superuser.com"),
        ("My Super Team", "mysuperteam@superuser.com"),
        ("TEAM BIG", "teambig@superuser.com"),
        (
            "ThisIsAnExtremelyLongTeamNameThatExceedsThirtyCharacters",
            "thisisanextremelylongteamnamet@superuser.com",
        ),
        ("Crazy Team 123", "crazyteam123@superuser.com"),
        (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234",
            "abcdefghijklmnopqrstuvwxyz1234@superuser.com",
        ),
    ],
)
def test_generate_super_user_email(team_name, expected_email):
    result = _generate_super_user_email(team_name)
    assert result == expected_email
