import pytest

from core.services.admin_service import _generate_super_user_email


@pytest.mark.parametrize(
    "team_name, expected_email",
    [
        ("TeamA", "superuser@teama.com"),
        ("My Super Team", "superuser@mysuperteam.com"),
        ("TEAM BIG", "superuser@teambig.com"),
        (
            "ThisIsAnExtremelyLongTeamNameThatExceedsThirtyCharacters",
            "superuser@thisisanextremelylongteamnamet.com",
        ),
        ("Crazy Team 123", "superuser@crazyteam123.com"),
        (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234",
            "superuser@abcdefghijklmnopqrstuvwxyz1234.com",
        ),
    ],
)
def test_generate_super_user_email(team_name, expected_email):
    result = _generate_super_user_email(team_name)
    assert result == expected_email
