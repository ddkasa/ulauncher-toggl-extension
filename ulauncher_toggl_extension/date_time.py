from __future__ import annotations

import enum
import time
from datetime import date, datetime, timedelta, timezone
from functools import cache


class TimeFrame(enum.Enum):
    DAY = enum.auto()
    WEEK = enum.auto()
    MONTH = enum.auto()


TIME_FORMAT = frozenset({"AM", "PM", "am", "pm"})

DT_FORMATS: tuple[str, ...] = (
    "%Y-%m-%dT%I:%M:%S %p",
    "%Y-%m-%dT%I:%M %p",
    "%I:%M:%S %p",
    "%I:%M %p",
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%H:%M:%S",
    "%H:%M",
    "%dT%H:%M",
    "%dT%I:%M %p",
)

TIME_SUFFIX: dict[str, str] = {
    "h": "hours",
    "m": "minutes",
    "s": "seconds",
    "ms": "milliseconds",
    "w": "weeks",
    "d": "days",
    "y": "years",
}

ORDINALS: dict[int, str] = {
    1: "st",
    2: "nd",
    3: "rd",
}


def display_dt(ts: datetime) -> str:
    ordinal = ORDINALS.get(ts.day % 10, "th")
    return ts.astimezone(get_local_tz()).strftime(f"%H:%M %A, %-d{ordinal} of %B %Y")


def parse_timedelta(ts_text: str) -> timedelta:
    for fmt, keyword in TIME_SUFFIX.items():
        if ts_text.endswith(fmt):
            ts_text = ts_text.removesuffix(fmt)
            return timedelta(**{keyword: int(ts_text)})

    msg = f"Could not find a time format that matched the supplied string. {ts_text}"
    raise ValueError(msg)


def parse_datetime(ts_text: str) -> datetime:
    """Utility to parse various dateformats into datetime objects."""
    for fmt in DT_FORMATS:
        try:
            dt = datetime.strptime(ts_text, fmt)  # noqa: DTZ007
        except ValueError:
            continue

        if dt.year == 1900:  # noqa: PLR2004
            today = date.today()  # noqa: DTZ011
            dt = dt.replace(
                year=today.year,
                month=today.month,
                day=today.day,
            )
        return localize_timezone(dt)

    msg = f"Could not find a dt format that matched the supplied string. {ts_text}"
    raise ValueError(msg)


@cache
def get_local_tz() -> timezone:
    return timezone(
        timedelta(hours=time.timezone + time.daylight),
        name=time.tzname[time.daylight],
    )


def localize_timezone(ts: datetime) -> datetime:
    return datetime(
        year=ts.year,
        month=ts.month,
        day=ts.day,
        hour=ts.hour,
        minute=ts.minute,
        second=ts.second,
        tzinfo=get_local_tz(),
    )


if __name__ == "__main__":
    pass
