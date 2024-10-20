"""Module that contains all the commands built on top of the API wrapper.

Abstract Classes:
    - Command
    - Search Command
    - SubCommand

Utility Dataclasses:
    - QueryParameters
    - ActionEnum

Classes:
    - CurrentTracker
    - ContinueCommand
    - StartCommand
    - AddCommand
    - DeleteCommand
    - EditCommand
    - StopCommand
    - ListTrackerCommand
    - Search Trackers (Not implemented yet)
    - ProjectCommands
        - List Projects
        - Add Project
        - Edit Project
        - Delete Project
        - Search Projects (Not implemented yet)
    - ClientCommands
        - List Clients
        - Add Client
        - Edit Client
        - Delete Client
        - Search Clients (Not implemented yet)
    - TagCommands:
        - List Tags
        - Add Tag
        - Edit Tag
        - Delete Tag
        - Search Tags (Not implemented yet)
    - ReportCommands:
        - Daily Report
        - Weekly Report
        - Monthly Report
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
    "ReportCommand",
    "StartCommand",
    "StopCommand",
    "TagCommand",
)
