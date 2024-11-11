from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ulauncher_toggl_extension.images import TIP_IMAGES, TipSeverity

from .client import (
    AddClientCommand,
    ClientCommand,
    DeleteClientCommand,
    EditClientCommand,
    ListClientCommand,
    RefreshClientCommand,
)
from .meta import Command, QueryResults
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
    from toggl_api.models import TogglClass

    from ulauncher_toggl_extension.extension import TogglExtension
    from ulauncher_toggl_extension.query import Query


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
        ClientCommand.PREFIX + " " + RefreshClientCommand.PREFIX: RefreshClientCommand,
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
    ALIASES = ("hint", "guide")
    ICON = TIP_IMAGES[TipSeverity.INFO]

    OPTIONS = ()

    __slots__ = ("hints",)

    def __init__(self, extension: TogglExtension) -> None:
        super().__init__(extension)
        self.hints = extension.hints

    def preview(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        del kwargs
        if not self.hints:
            return []

        self.amend_query(query.raw_args)

        return [
            QueryResults(
                self.ICON,
                self.PREFIX.title(),
                "Show help.",
                f"{self.prefix} {self.PREFIX}",
            ),
        ]

    def view(self, query: Query, **kwargs: Any) -> list[QueryResults]:
        del kwargs
        self.amend_query(query.raw_args)
        if query.subcommand == "help":
            return self.hint()

        cmd = f"{query.subcommand}"
        if len(query.raw_args) >= 4:  # noqa: PLR2004  # NOTE: Help for subcommands.
            cmd += f" {query.raw_args[3]}"

        hints = self.HINT_COMMANDS.get(cmd)
        if hints:
            return hints.hint()

        return [
            QueryResults(
                self.ICON,
                "Usage",
                "tgl help <command>",
            ),
            QueryResults(
                TIP_IMAGES[TipSeverity.ERROR],
                "Go Back",
                "Go back to the default command.",
                f"{self.prefix} ",
            ),
        ]

    def handle(self, query: Query, **kwargs: Any) -> bool:  # noqa: PLR6301
        del query, kwargs
        return True

    def get_models(self, *args: Any, **kwargs: Any) -> list[TogglClass]:
        raise NotImplementedError

    def get_model(self, *args: Any, **kwargs: Any) -> TogglClass | None:
        raise NotImplementedError
