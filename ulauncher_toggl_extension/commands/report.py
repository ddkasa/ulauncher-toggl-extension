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


