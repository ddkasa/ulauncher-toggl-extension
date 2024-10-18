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
        start = kwargs.pop("start")
        if start is None:
            return False

        frame = self.get_frame(start)
        body = ReportBody(start_date=frame.start.date(), end_date=frame.end.date())

        suffix = kwargs.get("format", self.report_format)

        try:
            report = self.endpoint.export_report(body, suffix)
        except (HTTPStatusError, ValueError) as err:
            self.handle_error(err)
            return False

        self.save_report(report, start, suffix, kwargs.get("path"))

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
                        start=previous_date,
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


