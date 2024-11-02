import pytest
from toggl_api import JSONCache, ProjectEndpoint

from ulauncher_toggl_extension.commands.project import (
    AddProjectCommand,
    DeleteProjectCommand,
    EditProjectCommand,
    ListProjectCommand,
    ProjectCommand,
    RefreshProjectCommand,
)


@pytest.mark.integration
def test_refresh_project_command(dummy_ext, create_project, faker):
    endpoint = ProjectEndpoint(
        dummy_ext.workspace_id,
        dummy_ext.auth,
        JSONCache(dummy_ext.cache_path),
    )
    old_name = create_project.name
    create_project.name = faker.name()
    endpoint.cache.update_entries(create_project)
    endpoint.cache.commit()

    cmd = RefreshProjectCommand(dummy_ext)

    assert endpoint.cache.find_entry(create_project).name == create_project.name

    cmd.handle([], model=create_project)

    assert endpoint.cache.find_entry(create_project).name == old_name


@pytest.mark.unit
def test_project_subcommand(dummy_ext):
    cmd = ProjectCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert cmd.view(query)


@pytest.mark.integration
def test_add_project_command(dummy_ext, create_project, helper):
    cmd = AddProjectCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert cmd.view(query)

    assert helper(create_project.name, cmd) is not None


@pytest.mark.integration
def test_list_project_command(dummy_ext):
    cmd = ListProjectCommand(dummy_ext)

    query = []

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration
def test_edit_project_command(dummy_ext, create_project, faker, helper):
    cmd = EditProjectCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)

    desc = faker.name()
    assert cmd.handle(query, model=create_project, description=desc)
    assert helper(desc, cmd) is not None


@pytest.mark.integration
def test_delete_project_command(dummy_ext, create_project, helper):
    cmd = DeleteProjectCommand(dummy_ext)

    query = []
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    assert cmd.handle(query, model=create_project)
    assert helper(create_project.name, cmd) is None
