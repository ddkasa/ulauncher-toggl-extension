# ruff: noqa: DTZ001

from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from ulauncher_toggl_extension.date_time import (
    DT_FORMATS,
    TimeFrame,
    display_dt,
    get_caps,
    get_ordinal,
    localize_timezone,
    parse_datetime,
    parse_timedelta,
)


@pytest.mark.parametrize(
    ("date", "expected"),
    [
        (
            datetime(2024, 6, 1, 5, 2, tzinfo=timezone.utc),
            "05:02 Saturday, 1st of June 2024",
        ),
        (
            datetime(2024, 6, 2, 5, 2, tzinfo=timezone.utc),
            "05:02 Sunday, 2nd of June 2024",
        ),
        (
            datetime(2024, 6, 3, 5, 2, tzinfo=timezone.utc),
            "05:02 Monday, 3rd of June 2024",
        ),
        (
            datetime(2024, 6, 4, 5, 2, tzinfo=timezone.utc),
            "05:02 Tuesday, 4th of June 2024",
        ),
        (
            datetime(2024, 6, 13, 5, 2, tzinfo=timezone(timedelta(hours=5))),
            "00:02 Thursday, 13th of June 2024",
        ),
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


@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1, "st"),
        (2, "nd"),
        (3, "rd"),
        (4, "th"),
        (11, "th"),
        (12, "th"),
        (13, "th"),
        (25, "th"),
    ],
)
def test_ordinal(value, expected):
    assert get_ordinal(value) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    ("frame", "ts", "start", "end"),
    [
        (TimeFrame.DAY, 27, 27, 27),
        (TimeFrame.WEEK, 27, 21, 27),
        (TimeFrame.WEEK, 22, 21, 22),
        (TimeFrame.MONTH, 25, 1, 25),
        (TimeFrame.MONTH, 31, 1, 31),
    ],
)
def test_get_caps(frame, ts, start, end):
    with patch("ulauncher_toggl_extension.date_time.date") as mock_date:
        mock_date.today.return_value = date(2024, 10, ts)
        mock_date.side_effect = date

        s, e = get_caps(date(2024, 10, ts), frame)
        assert s.day == start
        assert e.day == end
