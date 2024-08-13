# Development

## Basic Environment
- Development is ran through Poetry.
 
1. `git clone https://github.com/ddkasa/ulauncher-toggl-extension`
2. `cd toggl-api-wrapper`
3. `$ poetry shell` 
4. `$ poetry install`

- Lint with `ruff ulauncher_toggl_extension`
- Check typing with `$ mypy ulauncher_toggl_extension`


### Testing

- All tests are run through `pytest`.
- Basic unit tests through `pytest -m unit`.
- Integration tests through `pytest -m integration`.


## Notes

- Additional system dependencies may need to be installed.
    - If on Fedora [this](https://gitlab.gnome.org/alicem/jhbuild-steps/-/wikis/JHBuild-on-Fedora) might be required.
