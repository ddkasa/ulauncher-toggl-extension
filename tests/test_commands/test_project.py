import pytest

from ulauncher_toggl_extension.commands.project import (
    AddProjectCommand,
    DeleteProjectCommand,
    EditProjectCommand,
    ListProjectCommand,
    ProjectCommand,
)


@pytest.mark.unit()
def test_project_subcommand(dummy_ext):
    cmd = ProjectCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert cmd.view(query)


@pytest.mark.integration()
def test_add_project_command(dummy_ext):
    cmd = AddProjectCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert cmd.view(query)


@pytest.mark.integration()
def test_list_project_command(dummy_ext):
    cmd = ListProjectCommand(dummy_ext)

    query = []

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration()
def test_edit_project_command(dummy_ext):
    cmd = EditProjectCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration()
def test_delete_project_command(dummy_ext):
    cmd = DeleteProjectCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
