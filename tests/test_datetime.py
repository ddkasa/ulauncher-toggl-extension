# ruff: noqa: DTZ001

from datetime import datetime, timedelta, timezone

import pytest

from ulauncher_toggl_extension.date_time import (
    DT_FORMATS,
    display_dt,
    localize_timezone,
    parse_datetime,
    parse_timedelta,
)


@pytest.mark.parametrize(
    ("date", "expected"),
    [
        (datetime(2024, 6, 1, 5, 2), "05:02 Saturday, 1st of June 2024"),
        (datetime(2024, 6, 2, 5, 2), "05:02 Sunday, 2nd of June 2024"),
        (datetime(2024, 6, 3, 5, 2), "05:02 Monday, 3rd of June 2024"),
        (datetime(2024, 6, 4, 5, 2), "05:02 Tuesday, 4th of June 2024"),
    ],
)
@pytest.mark.unit
def test_display_dt(date, expected):
    assert display_dt(date) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("2h", timedelta(hours=2)),
        ("2s", timedelta(seconds=2)),
        ("2h2s", None),
        ("2w", timedelta(weeks=2)),
        ("2d", timedelta(days=2)),
        ("2m", timedelta(minutes=2)),
    ],
)
@pytest.mark.unit
def test_parse_timedelta(data, expected):
    if expected is not None:
        assert parse_timedelta(data) == expected
    else:
        with pytest.raises((ValueError,)):
            assert parse_timedelta(data)


@pytest.mark.unit
def test_parse_datetime(get_tz):
    now = datetime.now(tz=get_tz)

    comp = localize_timezone(now)

    for fmt in DT_FORMATS:
        formatted = now.strftime(fmt)
        dt = parse_datetime(formatted)
        if "Y" in fmt:
            assert dt.year == comp.year
        if "m" in fmt:
            assert dt.month == comp.month
        if "d" in fmt:
            assert dt.day == comp.day
        if "I" in fmt:
            assert dt.hour == comp.hour
        if "M" in fmt:
            assert dt.minute == comp.minute

    with pytest.raises((ValueError,)):
        assert parse_datetime("wadfwadad")


@pytest.mark.unit
def test_parse_localize(get_tz):
    now = datetime.now(tz=timezone.utc)

    assert localize_timezone(now).tzinfo == get_tz
