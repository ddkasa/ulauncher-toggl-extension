from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Optional

from httpx import HTTPStatusError
from toggl_api.reports import (
    DetailedReportEndpoint,
    PaginationOptions,
    ReportBody,
    ReportEndpoint,
    SummaryReportEndpoint,
    WeeklyReportEndpoint,
)

from ulauncher_toggl_extension.date_time import (
    NOON,
    ORDINALS,
    WEEKDAYS,
    DateTimeFrame,
    TimeFrame,
    get_local_tz,
)
from ulauncher_toggl_extension.images import REPORT_IMG

from .meta import Command, QueryParameters, SubCommand

if TYPE_CHECKING:
    from toggl_api.reports.reports import REPORT_FORMATS

    from ulauncher_toggl_extension.extension import TogglExtension


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
        endpoint = DetailedReportEndpoint(
            self.workspace_id,
            self.auth,
            include_time_entry_ids=False,
        )
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
    ALIASES = ("stats", "rep")
    ICON = REPORT_IMG
    EXPIRATION = None  # NOTE: Report endpoints don't have cache.
    FRAME: ClassVar[TimeFrame]
    ENDPOINT: ClassVar[type[ReportEndpoint]]

    __slots__ = ("report_format",)

    def __init__(self, extension: TogglExtension | Command) -> None:
        super().__init__(extension)
        self.report_format = getattr(extension, "report_format", "pdf")

    def get_models(self, **_) -> None:  # type: ignore[override]  # noqa: PLR6301
        msg = "Reports don't have models assocciated!"
        raise NotImplementedError(msg)

    def handle(self, query: list[str], **kwargs) -> bool:
        del query
        day = kwargs.pop("day")
        if day is None:
            return False

        frame = self.get_frame(day)
        body = ReportBody(start_date=frame.start.date(), end_date=frame.end.date())

        suffix = kwargs.get("format", self.report_format)

        try:
            report = self.endpoint.export_report(body, suffix)
        except (HTTPStatusError, ValueError) as err:
            self.handle_error(err)
            return False

        self.save_report(report, day, suffix, kwargs.get("path"))

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
            next_date = day.replace(month=day.month + diff)
        else:
            msg = "Target timeframe is not supported!"
            raise NotImplementedError(msg)

        return next_date if next_date.date() <= date.today() else None  # noqa: DTZ011

    def paginate_report(self, query: list[str], day: date) -> list[QueryParameters]:
        report: list[QueryParameters] = []

        previous_date = self.increment_date(day, increment=False)
        if previous_date:
            report.append(
                QueryParameters(
                    self.ICON,
                    f"View {self.format_datetime(previous_date)}",
                    None,
                    partial(
                        self.call_pickle,
                        method="view",
                        query=query,
                        day=previous_date,
                    ),
                    small=True,
                ),
            )
        next_date = self.increment_date(day)
        if next_date:
            report.append(
                QueryParameters(
                    self.ICON,
                    f"View {self.format_datetime(next_date)}",
                    None,
                    partial(
                        self.call_pickle,
                        method="view",
                        query=query,
                        day=next_date,
                    ),
                    small=True,
                ),
            )
        return report

    @classmethod
    def format_datetime(cls, day: date) -> str:
        del day
        return ""


class DailyReportCommand(ReportCommand):
    """View the daily breakdown."""

    PREFIX = "day"
    ALIASES = ("daily", "d")
    ICON = REPORT_IMG  # TODO: Custom image for each type of report.
    ENDPOINT = SummaryReportEndpoint
    FRAME = TimeFrame.DAY

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        day = kwargs.get("day") or datetime.now(tz=timezone.utc)
        kwargs["day"] = day
        self.amend_query(query)
        return [
            QueryParameters(
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

    def break_down_hours(self, day: date) -> list[int]:
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
            hours[start.hour] += diff
            remaining = time_data["seconds"] - diff
            hour = start.hour
            while remaining > 0:
                hour = (hour + 1) % 24
                hours[hour] += min(3600, remaining)
                remaining -= 3600

        return hours

    def summary(self, day: date) -> list[QueryParameters]:
        hours = self.break_down_hours(day)
        results = [
            QueryParameters(
                self.ICON,
                f"{h}{'pm' if h >= NOON else 'am'}: {min(60, t // 60)}min",
                small=True,
            )
            for h, t in enumerate(hours)
            if t
        ]

        results.append(
            QueryParameters(
                self.ICON,
                "Total Hours",
                f"{round(sum(hours) / 3600, 2)} hours",
                small=True,
            ),
        )

        return results

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        day = kwargs.get("day") or datetime.now(tz=timezone.utc)
        kwargs["day"] = day
        suffix = kwargs.get("format", self.report_format)
        kwargs["format"] = suffix
        results = [
            QueryParameters(
                self.ICON,
                self.format_datetime(day),
                "Daily Breakdown",
            ),
            QueryParameters(
                self.ICON,
                "Export Report",
                f"Export report in {suffix} format.",
                partial(
                    self.call_pickle,
                    method="handle",
                    query=query,
                    **kwargs,
                ),
            ),
        ]
        results += self.summary(day)
        results += self.paginate_report(query, day)
        return results

    @classmethod
    def format_datetime(cls, day: date) -> str:
        ordinal = ORDINALS.get(day.day % 10, "th")
        return day.astimezone(get_local_tz()).strftime(f"%-d{ordinal} of %B %Y")


class WeeklyReportCommand(ReportCommand):
    """View the weekly breakdown."""

    PREFIX = "week"
    ALIASES = ("weekly", "w")
    ICON = REPORT_IMG  # TODO: Custom image for each type of report.
    ENDPOINT = WeeklyReportEndpoint
    FRAME = TimeFrame.WEEK

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        del kwargs
        self.amend_query(query)
        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                self.get_cmd(),
            ),
        ]

    def break_down_days(self, day: date) -> list[int]:
        days: list[int] = [0] * 7

        for tracker in self._fetch_break_down(self.get_frame(day)):
            time_data = tracker["time_entries"][0]
            start = datetime.fromisoformat(time_data["stop"])
            # FIX: If tracking over midnight this will cause issues
            days[start.weekday()] += time_data["seconds"]

        return days

    def summary(self, day: date) -> list[QueryParameters]:
        days = self.break_down_days(day)
        result = [
            QueryParameters(
                self.ICON,
                f"{WEEKDAYS[weekday]}: {round(d / 3600, 2)} hours",
                small=True,
            )
            for weekday, d in enumerate(days)
        ]
        result.append(
            QueryParameters(
                self.ICON,
                f"Total: {sum(days) // 3600} hours",
                small=True,
            ),
        )

        return result

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        day = kwargs.get("day", datetime.now(tz=timezone.utc))
        kwargs["day"] = day
        suffix = kwargs.get("format", self.report_format)
        kwargs["format"] = suffix

        results = [
            QueryParameters(
                self.ICON,
                self.format_datetime(day),
                "Weekly Breakdown",
            ),
            QueryParameters(
                self.ICON,
                "Export Report",
                f"Export report in {suffix} format.",
                partial(
                    self.call_pickle,
                    method="handle",
                    query=query,
                    **kwargs,
                ),
            ),
        ]
        results += self.summary(day)
        results.extend(self.paginate_report(query, day))
        return results

    @classmethod
    def format_datetime(cls, day: date) -> str:
        week = day.isocalendar().week
        return f"{week}{ORDINALS.get(week % 10, 'th')} week of {day.year}"


class MonthlyReportCommand(ReportCommand):
    """View the monthly breakdown."""

    PREFIX = "month"
    ALIASES = ("monthly", "m")
    ICON = REPORT_IMG  # TODO: Custom image for each type of report.
    ENDPOINT = SummaryReportEndpoint
    FRAME = TimeFrame.MONTH

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        del kwargs
        self.amend_query(query)
        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                self.__doc__,
                self.get_cmd(),
            ),
        ]

    def summary(self, day: date) -> list[QueryParameters]:
        frame = self.get_frame(day)
        total_hours = self.get_totals(frame)
        return [
            QueryParameters(
                self.ICON,
                "Total Hours",
                f"{total_hours} hours",
            ),
            QueryParameters(
                self.ICON,
                "Average Hours Per Day",
                f"{(total_hours / frame.end.day):.2f} hours",
            ),
        ]

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        day = kwargs.get("day") or datetime.now(tz=timezone.utc)
        kwargs["day"] = day
        suffix = kwargs.get("format", self.report_format)
        kwargs["format"] = suffix
        results = [
            QueryParameters(
                self.ICON,
                self.format_datetime(day),
                "Monthly Breakdown",
            ),
            QueryParameters(
                self.ICON,
                "Export Report",
                f"Export report in {suffix} format.",
                partial(
                    self.call_pickle,
                    method="handle",
                    query=query,
                    **kwargs,
                ),
            ),
        ]
        results += self.summary(day)
        results.extend(self.paginate_report(query, day))
        return results

    @classmethod
    def format_datetime(cls, day: date) -> str:
        return day.strftime("%B %Y")
