from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from functools import cache
from typing import Final

NOON: Final[int] = 12


class TimeFrame(enum.Enum):
    DAY = enum.auto()
    WEEK = enum.auto()
    MONTH = enum.auto()


@dataclass(frozen=True)
class DateTimeFrame:
    start: datetime = field()
    end: datetime = field()
    frame: TimeFrame = field()

    @classmethod
    def from_date(cls, day: date, frame: TimeFrame) -> DateTimeFrame:
        start, end = get_caps(day, frame)
        return cls(start, end, frame)


WEEKDAYS: Final[tuple[str, ...]] = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


TIME_FORMAT: Final[frozenset[str]] = frozenset({"AM", "PM", "am", "pm"})

DT_FORMATS: Final[tuple[str, ...]] = (
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

TIME_SUFFIX: Final[dict[str, str]] = {
    "h": "hours",
    "m": "minutes",
    "s": "seconds",
    "ms": "milliseconds",
    "w": "weeks",
    "d": "days",
    "y": "years",
}

ORDINALS: Final[dict[int, str]] = {
    1: "st",
    2: "nd",
    3: "rd",
}


def get_ordinal(number: int) -> str:
    if number in {11, 12, 13}:
        return "th"

    return ORDINALS.get(number % 10, "th")


def display_dt(ts: datetime) -> str:
    ordinal = get_ordinal(ts.day)
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


def get_caps(date_obj: date, frame: TimeFrame) -> tuple[datetime, datetime]:
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()

    if frame == TimeFrame.DAY:
        start = datetime.combine(
            date_obj,
            datetime.min.time(),
            tzinfo=timezone.utc,
        )
        stop = datetime.combine(
            date_obj,
            datetime.max.time(),
            tzinfo=timezone.utc,
        )
    elif frame == TimeFrame.WEEK:
        start_date = date_obj - timedelta(days=date_obj.weekday())
        start = datetime.combine(
            start_date,
            datetime.min.time(),
            tzinfo=timezone.utc,
        )
        stop = datetime.combine(
            start_date + timedelta(days=6),
            datetime.max.time(),
            tzinfo=timezone.utc,
        )
    elif frame == TimeFrame.MONTH:
        start = datetime.combine(
            date_obj.replace(day=1),
            datetime.min.time(),
            tzinfo=timezone.utc,
        )
        stop = datetime.combine(
            date(date_obj.year, (date_obj.month % 12) + 1, 1) - timedelta(days=1),
            datetime.max.time(),
            tzinfo=timezone.utc,
        )
    else:
        msg = "Target timeframe is not supported!"
        raise NotImplementedError(msg)

    tday = date.today()  # noqa: DTZ011
    if tday.month == stop.month and tday.year == stop.year:
        stop = stop.replace(day=min(tday.day, stop.day))

    return start, stop


def format_seconds(total_seconds: int) -> str:
    hours, minutes = divmod(total_seconds, 3600)
    return f"{hours}:{minutes // 60}"


if __name__ == "__main__":
    pass
