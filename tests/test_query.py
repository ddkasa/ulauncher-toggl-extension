import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ulauncher_toggl_extension.date_time import DT_FORMATS
from ulauncher_toggl_extension.query import Query


@pytest.mark.unit
def test_dataclass(faker, number):
    _id = number.randint(10, sys.maxsize)
    name = faker.name

    query = Query(["tgl", "edit"], _id, name)

    assert query.id == _id
    assert query.name == name

    assert query.command == "edit"


@pytest.mark.unit
def test_dataclass_tag_parse(faker, number):
    add_tags = ["+" + faker.name() for i in range(number.randint(10, 100))]
    rm_tags = ["-" + faker.name() for i in range(number.randint(10, 100))]

    query = Query("tgl edit" + " ".join(add_tags + rm_tags), tags=add_tags + rm_tags)

    assert len(query.tags) == len(add_tags) + len(rm_tags)
    assert len(query.rm_tags) == len(rm_tags)
    assert len(query.add_tags) == len(add_tags)


@pytest.mark.unit
def test_parsing_tags(query_parser, faker, number):
    add_tags = [
        "+" + faker.name().replace(" ", "_") for i in range(number.randint(10, 100))
    ]
    rm_tags = [
        "-" + faker.name().replace(" ", "_") for i in range(number.randint(10, 100))
    ]
    raw_tags = [
        faker.name().replace(" ", "_").lower() for i in range(number.randint(10, 100))
    ]
    args = ("tgl", "edit", "#" + ",".join(add_tags + rm_tags + raw_tags))
    total = add_tags + rm_tags + raw_tags
    query = query_parser.parse(" ".join(args))

    assert len(query.tags) == len(total)
    assert len(query.add_tags) == len(add_tags) + len(raw_tags)
    assert len(query.rm_tags) == len(rm_tags)


@pytest.mark.unit
def test_parsing_identifier_id(query_parser, faker, number):
    name = faker.name()
    _id = number.randint(10, sys.maxsize)

    args = " ".join(("tgl edit", f'"{name}"', f":{_id}", f"${_id}", f"@{_id}"))

    query = query_parser.parse(args)

    assert query.id == _id
    assert query.name == name
    assert query.project == _id
    assert query.client == _id


@pytest.mark.unit
def test_parsing_identifier_name(query_parser, faker):
    name = faker.name()
    _id = faker.name()

    args = " ".join(("tgl edit", f':"{_id}"', f'"{name}"', f'@"{name}"', f'$"{_id}"'))

    query = query_parser.parse(args)

    assert query.id == _id
    assert query.name == name
    assert query.project == name
    assert query.client == _id


@pytest.mark.unit
def test_parsing_identifier_name_edge_cases(query_parser):
    name = "Testing - Challenge"

    args = " ".join(("tgl edit", f'"{name}"'))

    query = query_parser.parse(args)

    assert query.name == name
    assert query.sort_order


@pytest.mark.unit
def test_parsing_flags(query_parser):
    args = ("tgl", "edit", "distinct", "^-", "active", "private")

    query = query_parser.parse(" ".join(args))

    assert not query.distinct
    assert not query.active
    assert not query.private
    assert not query.refresh
    assert not query.sort_order


@pytest.mark.unit
def test_parsing_misc(query_parser):
    args = ("tgl edit", ".pdf", "~/test", "#d92b2b")

    query = query_parser.parse(" ".join(args))

    assert query.report_format == "pdf"
    assert query.path == Path.home() / "test"
    assert query.color == "#d92b2b"


@pytest.mark.unit
@pytest.mark.parametrize("fmt", DT_FORMATS)
def test_parse_datetime(query_parser, fmt):
    start = datetime.now().astimezone()
    stop = start + timedelta(hours=5)
    args = ("tgl edit", ">" + start.strftime(fmt), "<" + stop.strftime(fmt))

    query = query_parser.parse(" ".join(args))

    pstart = query.start.astimezone()
    pstop = query.stop.astimezone()

    assert pstart.date() == start.date()
    assert pstop.date() == stop.date()

    if "%I" in fmt:
        assert pstart.hour == start.hour
        assert pstop.hour == stop.hour

    if "%M" in fmt:
        assert pstart.minute == start.minute
        assert pstop.minute == stop.minute

    if "%S" in fmt:
        assert pstart.second == start.second
        assert pstop.second == stop.second


@pytest.mark.unit
@pytest.mark.parametrize(
    ("fmt", "expected"),
    [
        ("2h", timedelta(hours=2)),
        ("2s", timedelta(seconds=2)),
        ("2h2s", None),
        ("2w", timedelta(weeks=2)),
        ("2d", timedelta(days=2)),
        ("2m", timedelta(minutes=2)),
    ],
)
def test_parse_timedelta(query_parser, fmt, expected):
    args = ("tgl add", ">" + fmt + "<")

    query = query_parser.parse(" ".join(args))

    assert query.duration == expected


@pytest.mark.unit
def test_dt_edge_cases(query_parser):
    args = ("tgl edit", ">5:20", "<4:20", ">5h<")

    query = query_parser.parse(" ".join(args))

    assert isinstance(query.start, datetime)
    assert query.stop is None
    assert query.duration == timedelta(hours=5)

    args = ("tgl add", ">5:20", "<6:20", ">5h<")

    query = query_parser.parse(" ".join(args))
    assert isinstance(query.start, datetime)
    assert isinstance(query.stop, datetime)
    assert query.duration is None

    args = ("tgl edit", ">-5h<")

    query = query_parser.parse(" ".join(args))
    assert query.duration is None
