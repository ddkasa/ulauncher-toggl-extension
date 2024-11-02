"""Module that contains all the commands built on top of the API wrapper.

Abstract Classes:
    - Command
    - Search Command
    - SubCommand

Utility Dataclasses:
    - QueryParameters
    - ActionEnum

Classes:
    - CurrentTrackerCommand
    - ContinueCommand
    - StartCommand
    - AddCommand
    - DeleteCommand
    - EditCommand
    - StopCommand
    - ListTrackerCommand
    - RefreshCommand
    - Search Trackers (Not implemented yet)
    - ProjectCommand
        - ListProjectCommand
        - AddProjectCommand
        - EditProjectCommand
        - DeleteProjectCommand
        - RefreshProjectCommand
        - Search Projects (Not implemented yet)
    - ClientCommand
        - ListClientCommand
        - AddClientCommand
        - EditClientCommand
        - DeleteClientCommand
        - RefreshClientCommand
        - Search Clients (Not implemented yet)
    - TagCommand:
        - ListTagCommand
        - AddTagCommand
        - EditTagCommand
        - DeleteTagCommand
        - SearchTags (Not implemented yet)
    - ReportCommand:
        - DailyReportCommand
        - WeeklyReportCommand
        - MonthlyReportCommand
"""

from .client import AddClientCommand, ClientCommand, DeleteClientCommand
from .help import HelpCommand
from .meta import ActionEnum, Command, QueryParameters
from .project import AddProjectCommand, DeleteProjectCommand, ProjectCommand
from .report import ReportCommand
from .tag import AddTagCommand, DeleteTagCommand, TagCommand
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

__all__ = (
    "ActionEnum",
    "AddClientCommand",
    "AddCommand",
    "AddProjectCommand",
    "AddTagCommand",
    "ClientCommand",
    "Command",
    "ContinueCommand",
    "CurrentTrackerCommand",
    "DeleteClientCommand",
    "DeleteCommand",
    "DeleteProjectCommand",
    "DeleteTagCommand",
    "EditCommand",
    "HelpCommand",
    "ListCommand",
    "ProjectCommand",
    "QueryParameters",
    "RefreshCommand",
    "ReportCommand",
    "StartCommand",
    "StopCommand",
    "TagCommand",
)
