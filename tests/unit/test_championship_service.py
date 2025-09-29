from datetime import date

from bounded_contexts.championship.schemas import ChampionshipUpdate
from bounded_contexts.championship.service import _changed_any_field_but_one


def test_changed_any_field_but_one(mock_championship_gen):
    champ = mock_championship_gen(
        name="Original",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 2, 2),
        is_league_format=True,
    )

    update_data = ChampionshipUpdate(
        name="Editando",
        start_date=date(2018, 3, 3),
        end_date=date(2018, 4, 4),
        is_league_format=False,
    )
    assert _changed_any_field_but_one(champ, update_data, "end_date") is True

    update_data = ChampionshipUpdate(
        name=champ.name,
        start_date=date(2018, 3, 3),
        end_date=date(2018, 4, 4),
        is_league_format=False,
    )
    assert _changed_any_field_but_one(champ, update_data, "end_date") is True

    update_data = ChampionshipUpdate(
        name=champ.name,
        start_date=champ.start_date,
        end_date=date(2025, 4, 4),
        is_league_format=False,
    )
    assert _changed_any_field_but_one(champ, update_data, "end_date") is True

    update_data = ChampionshipUpdate(
        name=champ.name,
        start_date=champ.start_date,
        end_date=date(2025, 4, 4),
        is_league_format=champ.is_league_format,
    )
    assert _changed_any_field_but_one(champ, update_data, "end_date") is False
