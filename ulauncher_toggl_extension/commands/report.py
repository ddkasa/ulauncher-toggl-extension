from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta, timezone
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Optional

from httpx import HTTPStatusError, codes
from toggl_api.reports import (
    DetailedReportEndpoint,
    PaginationOptions,
    ReportBody,
    ReportEndpoint,
    SummaryReportEndpoint,
)

from ulauncher_toggl_extension.date_time import (
    NOON,
    WEEKDAYS,
    DateTimeFrame,
    TimeFrame,
    get_local_tz,
    get_ordinal,
)
from ulauncher_toggl_extension.images import REPORT_IMG

from .meta import Command, QueryResults, SubCommand

if TYPE_CHECKING:
    from toggl_api.reports.reports import REPORT_FORMATS

    from ulauncher_toggl_extension.query import Query


class ReportMixin(Command):
    """Helper class for adding report functionality to other classes."""

    def get_totals(self, span: DateTimeFrame) -> float:
        endpoint = DetailedReportEndpoint(self.workspace_id, self.auth)

        body = ReportBody(span.start.date(), span.end.date())
        try:
            totals = endpoint.totals_report(
                body,
                granularity=str(span.frame.name.lower()),  # type: ignore[arg-type]
            )
        except HTTPStatusError as err:
            self.handle_error(err)
            return 0.0

        return round(totals.get("seconds", 0) / 3600, 2)

    def _break_down_helper(
        self,
        endpoint: DetailedReportEndpoint,
        body: ReportBody,
        trackers: list[dict],
        next_options: Optional[PaginationOptions] = None,
    ) -> PaginationOptions | None:
        next_options = next_options or PaginationOptions(250)
        try:
            search = endpoint.search_time_entries(body, next_options)
        except HTTPStatusError as err:
            self.handle_error(err)
            return None
        trackers.extend(search.result)
        return search.next_options()

    def _fetch_break_down(self, span: DateTimeFrame, **query) -> list[dict]:
        del query
        body = ReportBody(
            span.start.date(),
            span.end.date(),
            include_time_entry_ids=False,
        )
        trackers: list[dict] = []
        endpoint = DetailedReportEndpoint(self.workspace_id, self.auth)
        search = self._break_down_helper(endpoint, body, trackers)

        while (
            search is not None
            and isinstance(search.next_id, int)
            and isinstance(search.next_row, int)
        ):
            search = self._break_down_helper(endpoint, body, trackers, search)

        return trackers


class ReportCommand(SubCommand, ReportMixin):
    """Subcommand for all reports."""

    PREFIX = "report"
    ALIASES = ("stats", "rep", "statistics")
    ICON = REPORT_IMG
    EXPIRATION = None  # NOTE: Report endpoints don't have cache.
    FRAME: ClassVar[TimeFrame]
    ENDPOINT: ClassVar[type[ReportEndpoint]]
    OPTIONS = (">", "~")

    __slots__ = ("report_format",)

    def get_models(self, **_) -> None:  # type: ignore[override]  # noqa: PLR6301
        msg = "Reports don't have models assocciated!"
        raise NotImplementedError(msg)

    def get_model(self, **_) -> None:  # type: ignore[override]  # noqa: PLR6301
        msg = "Reports don't have models assocciated!"
        raise NotImplementedError(msg)

    def handle(self, query: Query, **kwargs: Any) -> bool:
        start = kwargs.pop("start", query.start)
        if start is None:
            return False

        frame = self.get_frame(start)
        body = ReportBody(start_date=frame.start.date(), end_date=frame.end.date())

        try:
            report = self.endpoint.export_report(body, query.report_format)
        except ValueError as err:
            self.handle_error(err)
            return False
        except HTTPStatusError as err:
            self.handle_error(err)
            return (
                err.response.status_code == codes.BAD_REQUEST
                and err.response.text == '"Summary data is empty"'
            )

        self.save_report(report, start, query.report_format, query.path)

        return True

    def save_report(
        self,
        data: bytes,
        day: date,
        suffix: REPORT_FORMATS,
        path: Optional[Path] = None,
    ) -> None:
        path = path or Path.home() / ".cache/ulauncher_toggl_extension/report/"

        path.mkdir(parents=True, exist_ok=True)
        # TODO: DEFAULT_FORMAT user set
        path /= f"{day.date().isoformat()}_{self.FRAME.name.lower()}_report.{suffix}"  # type: ignore[operator]

        with path.open("wb") as file:
            file.write(data)

        self.notification(f"Saved a {suffix} report at {path}")

    @classmethod
    def get_frame(cls, day: date) -> DateTimeFrame:
        return DateTimeFrame.from_date(day, cls.FRAME)

    @property
    def endpoint(self) -> ReportEndpoint:
        return self.ENDPOINT(self.workspace_id, self.auth)

    @classmethod
    def increment_date(cls, day: date, *, increment: bool = True) -> date | None:
        diff = 1 if increment else -1
        if cls.FRAME == TimeFrame.DAY:
            next_date = day + timedelta(days=diff)
        elif cls.FRAME == TimeFrame.WEEK:
            next_date = day + timedelta(weeks=diff)
        elif cls.FRAME == TimeFrame.MONTH:
            _, month = calendar.monthrange(day.year, day.month)
            next_date = day + timedelta(days=month * diff)
        else:
            msg = "Target timeframe is not supported!"
            raise NotImplementedError(msg)

        if isinstance(day, datetime):
            next_date = next_date.date()

        return next_date if next_date <= date.today() else None  # noqa: DTZ011

    def paginate_report(self, query: Query, day: date) -> list[QueryResults]:
        report: list[QueryResults] = []

        previous_date = self.increment_date(day, increment=False)
        if previous_date:
            report.append(
                QueryResults(
                    self.ICON,
                    f"View {self.format_datetime(previous_date)}",
                    None,
                    partial(
                        self.call_pickle,
                        method="view",
                        query=query,
                        start=previous_date,
                    ),
                    small=True,
                ),
            )
        next_date = self.increment_date(day)
        if next_date:
            report.append(
                QueryResults(
                    self.ICON,
                    f"View {self.format_datetime(next_date)}",
                    None,
                    partial(
                        self.call_pickle,
                        method="view",
                        query=query,
                        start=next_date,
                    ),
                    small=True,
                ),
            )
        return report

    @classmethod
    def format_datetime(cls, day: date) -> str:
        del day
        return ""

    @classmethod
    def _find_start(cls, query: Query, **kwargs) -> datetime:
        start = kwargs.get("start") or query.start or datetime.now(tz=timezone.utc)
        kwargs["start"] = start
        return start


class DailyReportCommand(ReportCommand):
    """View the daily breakdown."""

    PREFIX = "day"
    ALIASES = ("daily", "dy")
    ICON = REPORT_IMG  # TODO: Custom image for each type of report.
    ENDPOINT = SummaryReportEndpoint
    FRAME = TimeFrame.DAY

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        query.start = self._find_start(query, **kwargs)
        self.amend_query(query.raw_args)
        return [
            QueryResults(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                self.get_cmd(),
                partial(
                    self.call_pickle,
                    method="handle",
                    query=query,
                    **kwargs,
                ),
            ),
        ]

    def break_down(self, day: date) -> list[int]:
        hours: list[int] = [0] * 24

        for tracker in self._fetch_break_down(self.get_frame(day)):
            time_data = tracker["time_entries"][0]

            start = datetime.fromisoformat(time_data["start"])
            next_hour = start.replace(
                second=0,
                microsecond=0,
                minute=0,
            ) + timedelta(hours=1)
            diff = int((next_hour - start).total_seconds())
            hours[start.hour] += min(diff, time_data["seconds"])

            remaining = time_data["seconds"] - diff
            hour = start.hour + 1
            while remaining > 0 and hour < 24:  # noqa: PLR2004
                hours[hour] += min(3600, remaining)
                remaining -= 3600
                hour += 1

        return hours

    def summary(self, day: date) -> list[QueryResults]:
        hours = self.break_down(day)
        results = [
            QueryResults(
                self.ICON,
                f"{h}{'pm' if h >= NOON else 'am'}: {min(60, t // 60)}min",
                small=True,
            )
            for h, t in enumerate(hours)
            if t
        ]

        results.append(
            QueryResults(
                self.ICON,
                "Total Hours",
                f"{round(sum(hours) / 3600, 2)} hours",
                small=True,
            ),
        )

        return results

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        query.start = self._find_start(query, **kwargs)
        results = [
            QueryResults(
                self.ICON,
                self.format_datetime(query.start),
                "Daily Breakdown",
            ),
            QueryResults(
                self.ICON,
                "Export Report",
                f"Export report in {query.report_format} format.",
                partial(
                    self.call_pickle,
                    method="handle",
                    query=query,
                    **kwargs,
                ),
            ),
        ]
        results += self.summary(query.start)
        results += self.paginate_report(query, query.start)
        return results

    @classmethod
    def format_datetime(cls, day: date) -> str:
        if isinstance(day, datetime):
            day = day.astimezone(get_local_tz())
        return day.strftime(f"%-d{get_ordinal(day.day)} of %B %Y")


class WeeklyReportCommand(ReportCommand):
    """View the weekly breakdown."""

    PREFIX = "week"
    ALIASES = ("weekly", "wk")
    ICON = REPORT_IMG  # TODO: Custom image for each type of report.
    ENDPOINT = SummaryReportEndpoint
    FRAME = TimeFrame.WEEK

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        query.start = self._find_start(query, **kwargs)
        self.amend_query(query.raw_args)
        return [
            QueryResults(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                self.get_cmd(),
                partial(
                    self.call_pickle,
                    method="handle",
                    query=query,
                    **kwargs,
                ),
            ),
        ]

    def break_down(self, day: date) -> list[int]:
        days: list[int] = [0] * 7
        for tracker in self._fetch_break_down(self.get_frame(day)):
            time_data = tracker["time_entries"][0]

            start = datetime.fromisoformat(time_data["start"])
            next_day = (start + timedelta(days=1)).replace(
                second=0,
                microsecond=0,
                minute=0,
                hour=0,
            )
            diff = int((next_day - start).total_seconds())
            days[start.weekday()] += min(diff, time_data["seconds"])

            total = time_data["seconds"] - diff
            weekday = start.weekday() + 1
            while total > 0 and weekday <= 6:  # noqa: PLR2004
                days[weekday] += min(86400, total)
                total -= 86400
                weekday += 1

        return days

    def summary(self, day: date) -> list[QueryResults]:
        days = self.break_down(day)
        result = [
            QueryResults(
                self.ICON,
                f"{WEEKDAYS[weekday]}: {round(d / 3600, 2)} hours",
                small=True,
            )
            for weekday, d in enumerate(days)
            if d
        ]
        result.append(
            QueryResults(
                self.ICON,
                f"Total: {sum(days) // 3600} hours",
                small=True,
            ),
        )

        return result

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        query.start = self._find_start(query, **kwargs)

        results = [
            QueryResults(
                self.ICON,
                self.format_datetime(query.start),
                "Weekly Breakdown",
            ),
            QueryResults(
                self.ICON,
                "Export Report",
                f"Export report in {query.report_format} format.",
                partial(
                    self.call_pickle,
                    method="handle",
                    query=query,
                    **kwargs,
                ),
            ),
        ]
        results += self.summary(query.start)
        results += self.paginate_report(query, query.start)
        return results

    @classmethod
    def format_datetime(cls, day: date) -> str:
        if isinstance(day, datetime):
            day = day.astimezone(get_local_tz())
        week = day.isocalendar().week
        return f"{week}{get_ordinal(week)} week of {day.year}"


class MonthlyReportCommand(ReportCommand):
    """View the monthly breakdown."""

    PREFIX = "month"
    ALIASES = ("monthly",)
    ICON = REPORT_IMG  # TODO: Custom image for each type of report.
    ENDPOINT = SummaryReportEndpoint
    FRAME = TimeFrame.MONTH

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        query.start = self._find_start(query, **kwargs)
        self.amend_query(query.raw_args)
        return [
            QueryResults(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                self.get_cmd(),
                partial(
                    self.call_pickle,
                    method="handle",
                    query=query,
                    **kwargs,
                ),
            ),
        ]

    def break_down(self, day: date) -> tuple[int, int]:
        first, second = 0, 0

        _, number_of_days = calendar.monthrange(day.year, day.month)
        mid_point = number_of_days // 2

        for tracker in self._fetch_break_down(self.get_frame(day)):
            time_data = tracker["time_entries"][0]

            start = datetime.fromisoformat(time_data["start"])
            if start.day <= mid_point:
                first += time_data["seconds"]
            else:
                second += time_data["seconds"]
        return first, second

    def summary(self, day: date) -> list[QueryResults]:
        frame = self.get_frame(day)
        first_half, second_half = self.break_down(day)
        total_hours = (first_half + second_half) / 3600
        return [
            QueryResults(
                self.ICON,
                "Total Hours",
                f"{total_hours:.2f} hours",
            ),
            QueryResults(
                self.ICON,
                "Average Hours Per Day",
                f"{(total_hours / frame.end.day):.2f} hours",
            ),
            QueryResults(
                self.ICON,
                f"First Half: {(first_half / 3600):.2f} hours",
                small=True,
            ),
            QueryResults(
                self.ICON,
                f"Second Half: {(second_half / 3600):.2f} hours",
                small=True,
            ),
        ]

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        query.start = self._find_start(query, **kwargs)
        results = [
            QueryResults(
                self.ICON,
                self.format_datetime(query.start),
                "Monthly Breakdown",
            ),
            QueryResults(
                self.ICON,
                "Export Report",
                f"Export report in {query.report_format} format.",
                partial(
                    self.call_pickle,
                    method="handle",
                    query=query,
                    **kwargs,
                ),
            ),
        ]
        results += self.summary(query.start)
        results.extend(self.paginate_report(query, query.start))
        return results

    @classmethod
    def format_datetime(cls, day: date) -> str:
        if isinstance(day, datetime):
            day = day.astimezone(get_local_tz())
        return day.strftime("%B %Y")
