from __future__ import annotations

from typing import TYPE_CHECKING

from ulauncher_toggl_extension.images import TIP_IMAGES, TipSeverity

from .client import (
    AddClientCommand,
    ClientCommand,
    DeleteClientCommand,
    EditClientCommand,
    ListClientCommand,
)
from .meta import Command, QueryParameters
from .project import (
    AddProjectCommand,
    DeleteProjectCommand,
    EditProjectCommand,
    ListProjectCommand,
    ProjectCommand,
    RefreshProjectCommand,
)
from .report import (
    DailyReportCommand,
    MonthlyReportCommand,
    ReportCommand,
    WeeklyReportCommand,
)
from .tag import (
    AddTagCommand,
    DeleteTagCommand,
    EditTagCommand,
    ListTagCommand,
    TagCommand,
)
from .tracker import (
    AddCommand,
    ContinueCommand,
    CurrentTrackerCommand,
    DeleteCommand,
    EditCommand,
    ListCommand,
    RefreshCommand,
    StartCommand,
    StopCommand,
)

if TYPE_CHECKING:
    from ulauncher_toggl_extension.extension import TogglExtension


class HelpCommand(Command):
    """Help command for general hints."""

    # REFACTOR: This could be automated.
    HINT_COMMANDS: dict[str, type[Command]] = {
        ContinueCommand.PREFIX: ContinueCommand,
        ListCommand.PREFIX: ListCommand,
        CurrentTrackerCommand.PREFIX: CurrentTrackerCommand,
        StopCommand.PREFIX: StopCommand,
        StartCommand.PREFIX: StartCommand,
        AddCommand.PREFIX: AddCommand,
        EditCommand.PREFIX: EditCommand,
        DeleteCommand.PREFIX: DeleteCommand,
        ProjectCommand.PREFIX: ProjectCommand,
        RefreshCommand.PREFIX: RefreshCommand,
        ProjectCommand.PREFIX + " " + ListProjectCommand.PREFIX: ListProjectCommand,
        ProjectCommand.PREFIX + " " + AddProjectCommand.PREFIX: AddProjectCommand,
        ProjectCommand.PREFIX + " " + DeleteProjectCommand.PREFIX: DeleteProjectCommand,
        ProjectCommand.PREFIX + " " + EditProjectCommand.PREFIX: EditProjectCommand,
        ProjectCommand.PREFIX
        + " "
        + RefreshProjectCommand.PREFIX: RefreshProjectCommand,
        ClientCommand.PREFIX: ClientCommand,
        ClientCommand.PREFIX + " " + ListClientCommand.PREFIX: ListClientCommand,
        ClientCommand.PREFIX + " " + AddClientCommand.PREFIX: AddClientCommand,
        ClientCommand.PREFIX + " " + DeleteClientCommand.PREFIX: DeleteClientCommand,
        ClientCommand.PREFIX + " " + EditClientCommand.PREFIX: EditClientCommand,
        TagCommand.PREFIX: TagCommand,
        TagCommand.PREFIX + " " + ListTagCommand.PREFIX: ListTagCommand,
        TagCommand.PREFIX + " " + AddTagCommand.PREFIX: AddTagCommand,
        TagCommand.PREFIX + " " + DeleteTagCommand.PREFIX: DeleteTagCommand,
        TagCommand.PREFIX + " " + EditTagCommand.PREFIX: EditTagCommand,
        ReportCommand.PREFIX: ReportCommand,
        ReportCommand.PREFIX + " " + DailyReportCommand.PREFIX: DailyReportCommand,
        ReportCommand.PREFIX + " " + WeeklyReportCommand.PREFIX: WeeklyReportCommand,
        ReportCommand.PREFIX + " " + MonthlyReportCommand.PREFIX: MonthlyReportCommand,
    }

    PREFIX = "help"
    ALIASES = ("h", "hint", "guide")
    ICON = TIP_IMAGES[TipSeverity.INFO]

    __slots__ = ("hints",)

    def __init__(self, extension: TogglExtension) -> None:
        super().__init__(extension)
        self.hints = extension.hints

    def preview(self, query: list[str], **kwargs) -> list[QueryParameters]:
        del kwargs
        if not self.hints:
            return []

        self.amend_query(query)

        return [
            QueryParameters(
                self.ICON,
                self.PREFIX.title(),
                "Show help.",
                f"{self.prefix} {self.PREFIX}",
            ),
        ]

    def view(self, query: list[str], **kwargs) -> list[QueryParameters]:
        del kwargs
        self.amend_query(query)
        if len(query) >= self.MIN_ARGS and query[-1] == self.PREFIX:
            return self.hint()

        cmd = " ".join(query[1:])
        hints = self.HINT_COMMANDS.get(cmd)
        if hints:
            return hints.hint()

        return [
            QueryParameters(
                self.ICON,
                "Usage",
                "tgl help <command>",
            ),
            QueryParameters(
                TIP_IMAGES[TipSeverity.ERROR],
                "Go Back",
                "Go back to the default command.",
                f"{self.prefix} ",
            ),
        ]

    def handle(self, query: list[str], **kwargs) -> bool:  # noqa: PLR6301
        del query, kwargs
        return True

    def get_models(self, **kwargs) -> None:  # type: ignore[override]
        raise NotImplementedError
