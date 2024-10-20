# Ulauncher Toggl Time Tracker Extension

![GitHub Tag](https://img.shields.io/github/v/tag/ddkasa/ulauncher-toggl-extension?style=for-the-badge)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/ddkasa/ulauncher-toggl-extension/.github%2Fworkflows%2Ftests.yaml?style=for-the-badge&link=https%3A%2F%2Fgithub.com%2Fddkasa%2Fulauncher-toggl-extension%2Factions%2Fworkflows%2Ftests.yaml)

> Extension for [Ulauncher](https://github.com/Ulauncher/Ulauncher/) heavily inspired by [Flow Toggl Plugin](https://github.com/JamesNZL/flow-toggl-plugin).

## Requirements & Installation

### Pre Requisites

1. [Ulauncher](https://github.com/Ulauncher/Ulauncher/) with 2.0 API
2. Tested on Python 3.10, 3.11, 3.12

### Installation

1. Install through Ulauncher GUI or clone the production branch into `~/.local/share/ulauncher/extensions/`
2. Setup your authentication. It checks in order of:
   1. Ulauncher Config Api Token
   2. Environment Variables
      - Either **TOGGL_API_TOKEN** or if using email **TOGGL_API_TOKEN** + **TOGGL_PASSWORD**
   3. _.togglrc_ in the default home location. Configuration from [Toggl CLI](https://github.com/AuHau/toggl-cli)
3. Set your default workspace inside the configuration or as an environment variable: **TOGGL_WORKSPACE_ID**
4. Customize any other settings inside the Ulauncher configuration
5. You're now ready to use the extension

> [!NOTE]
> This will install [Toggl Api Wrapper](https://pypi.org/project/toggl-api-wrapper/) on startup and update the dependency if needed. If you run into issues please check your root pip installation to see if the wrapper is present with `/usr/bin/pip list | grep toggl`.

## Usage

- Invoked in Ulauncher with the `tgl` prefix by default
- Check out the [usage guide](docs/guide.md) for more details
- Use `tgl help <command>` inside the extension to get more details on a specific command

### Supports

- **Trackers**
  1. Continuing a tracker
  2. Stopping a tracker
  3. Editing a tracker
  4. Starting a new tracker
  5. Adding a new tracker
  6. Deleting a tracker
  7. Listing all trackers
- **Projects**
  1. Listing your projects
  2. Adding projects
  3. Editing projects
  4. Deleting projects
- **Clients**
  1. Listing your clients
  2. Adding clients
  3. Editing clients
  4. Deleting clients
- **Tags**
  1. Listing your tags
  2. Adding tags
  3. Editing tags
  4. Deleting tags
- **Reports**
  1. View & export daily breakdown
  2. View & export weekly breakdown
  3. View & export monthly breakdown

# Contributing

See [CONTRIBUTING](docs/CONTRIBUTING.md)

# License

MIT. Look at the [LICENSE](LICENSE.md) for details
