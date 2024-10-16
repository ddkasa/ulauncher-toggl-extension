# Development

### Basic Environment

- Development is run through Poetry

1. `git clone https://github.com/ddkasa/ulauncher-toggl-extension`
2. `cd toggl-api-wrapper`
3. `$ poetry shell`
4. `$ poetry install`

- Lint with `ruff ulauncher_toggl_extension`
- Check typing with `mypy ulauncher_toggl_extension`
- Make sure to install pre-commit hook with `pre-commit install`

- In order to debug/test the extension inside Ulauncher:

1. Move extension into this folder:

```
~/.local/share/ulauncher/extensions/
```

2. Run:

```bash
VERBOSE=1 ULAUNCHER_WS_API=ws://127.0.0.1:5054/ulauncher-toggl-extension PYTHONPATH=/usr/lib/python3.12/site-packages /usr/bin/python3 /home/dk/.local/share/ulauncher/extensions/ulauncher-toggl-extension/main.py
```

### Testing

- All tests are run through `pytest`
- Basic unit tests through `pytest -m unit`
- Integration tests through `pytest -m integration`
- For multiple python versions run: `tox`

### Deployment

- Merge with **production** branch
- Make sure to add new development files to the _.gitattributes_ file

### Git

- Commit messages are based on [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)

### Notes

- More information on extension development [here](https://docs.ulauncher.io/en/stable/extensions/intro.html)
- Additional system dependencies may need to be installed.
  - If on Fedora [this](https://gitlab.gnome.org/alicem/jhbuild-steps/-/wikis/JHBuild-on-Fedora) might be required
