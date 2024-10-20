import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from ulauncher_toggl_extension.commands.report import (
    DailyReportCommand,
    MonthlyReportCommand,
    ReportCommand,
    WeeklyReportCommand,
)
from ulauncher_toggl_extension.date_time import DateTimeFrame, TimeFrame


@pytest.fixture
def load_model_data():
    local_path = Path.cwd() / "tests/data/detailed_response.json"
    with local_path.open("r", encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.unit
@pytest.mark.parametrize(
    "frame",
    [
        TimeFrame.DAY,
        TimeFrame.WEEK,
        TimeFrame.MONTH,
    ],
)
def test_get_totals(frame, dummy_ext, httpx_mock, number):
    cmd = ReportCommand(dummy_ext)
    value = number.randint(100, 100_000)
    httpx_mock.add_response(json={"seconds": value})
    assert cmd.get_totals(
        DateTimeFrame(
            datetime.now(tz=timezone.utc),
            datetime.now(tz=timezone.utc),
            frame,
        ),
    ) == round(value / 3600, 2)


@pytest.mark.unit
def test_get_totals_error(dummy_ext, httpx_mock):
    cmd = ReportCommand(dummy_ext)
    httpx_mock.add_response(status_code=450)
    assert (
        cmd.get_totals(
            DateTimeFrame(
                datetime.now(tz=timezone.utc),
                datetime.now(tz=timezone.utc),
                TimeFrame.DAY,
            ),
        )
        == 0.0
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "frame",
    [
        TimeFrame.DAY,
        TimeFrame.WEEK,
        TimeFrame.MONTH,
    ],
)
def test_fetch_break_down(frame, dummy_ext, httpx_mock, number):
    response = [{}] * number.randint(5, 100)
    httpx_mock.add_response(json=response)
    cmd = ReportCommand(dummy_ext)
    assert len(
        cmd._fetch_break_down(  # noqa: SLF001
            DateTimeFrame(
                datetime.now(tz=timezone.utc),
                datetime.now(tz=timezone.utc),
                frame,
            ),
        ),
    ) == len(response)


@pytest.mark.integration
@pytest.mark.parametrize(
    ("command", "fmt"),
    [
        (DailyReportCommand, "pdf"),
        (DailyReportCommand, "csv"),
        (WeeklyReportCommand, "pdf"),
        (WeeklyReportCommand, "csv"),
        (MonthlyReportCommand, "pdf"),
        (MonthlyReportCommand, "csv"),
    ],
)
def test_report_dump(command, fmt, dummy_ext, tmp_path):
    cmd = command(dummy_ext)
    tmp_path = Path(tmp_path)
    now = datetime.now(tz=timezone.utc)
    handle = cmd.handle([], start=now, format=fmt, path=tmp_path)
    assert handle
    assert (
        tmp_path / f"{now.date().isoformat()}_{cmd.FRAME.name.lower()}_report.{fmt}"
    ).exists()
