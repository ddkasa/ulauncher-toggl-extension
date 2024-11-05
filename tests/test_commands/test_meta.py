import pytest

from ulauncher_toggl_extension.commands.tracker import ListCommand


@pytest.mark.unit
@pytest.mark.parametrize(
    ("data", "static"),
    [(12, 0), (1, 0), (10, 2), (15, 1), (0, 0), (200, 2)],
)
def test_cmd_paginator(data, static, dummy_ext, dummy_query_parameters):
    params = dummy_query_parameters(data)

    static_param = dummy_query_parameters(static)

    cmd = ListCommand(dummy_ext)

    total = 0
    page = 1
    per_page = dummy_ext.max_results - (static + 1)
    while total < data:
        paginator = cmd._paginator([], params, static_param, page=page)  # noqa: SLF001
        assert all(
            p.name == e.name and p.description == e.description
            for p, e in zip(paginator[:per_page], params[per_page * page : per_page])
        )
        total += min(per_page, len(paginator))
        page += 1

    assert total == data
