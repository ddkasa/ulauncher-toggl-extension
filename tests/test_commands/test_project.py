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
def test_refresh_project_command(dummy_ext, create_project, faker, query_parser):
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

    assert cmd.get_model(create_project.id).name == create_project.name

    cmd.handle(query_parser.parse(f"tgl project refresh :{create_project.id}"))

    assert cmd.get_model(create_project.id).name == old_name


@pytest.mark.unit
def test_project_subcommand(dummy_ext, query_parser):
    cmd = ProjectCommand(dummy_ext)

    query = query_parser.parse("tgl project")
    assert cmd.preview(query)
    assert cmd.view(query)


@pytest.mark.integration
def test_add_project_command(dummy_ext, faker, query_parser):
    cmd = AddProjectCommand(dummy_ext)

    name = faker.name()
    query = query_parser.parse(f'tgl project add "{name}"')
    assert cmd.preview(query)
    assert cmd.view(query)

    assert cmd.handle(query)

    assert cmd.get_model(name) is not None


@pytest.mark.integration
def test_list_project_command(dummy_ext, query_parser):
    cmd = ListProjectCommand(dummy_ext)

    query = query_parser.parse("tgl project list")

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)


@pytest.mark.integration
def test_edit_project_command(dummy_ext, create_project, faker, query_parser):
    cmd = EditProjectCommand(dummy_ext)

    desc = faker.name()
    query = query_parser.parse(
        f'tgl project edit "{desc}" :{create_project.id} #0b83d9 refresh',
    )

    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)

    assert cmd.handle(query)
    assert cmd.get_model(desc) is not None


@pytest.mark.integration
def test_delete_project_command(dummy_ext, create_project, query_parser):
    cmd = DeleteProjectCommand(dummy_ext)

    query = query_parser.parse(f"tgl project delete :{create_project.id}")
    assert cmd.preview(query)
    assert isinstance(cmd.view(query), list)
    assert cmd.handle(query)
    assert cmd.get_model(create_project.name) is None
