# Ulauncher Toggl Time Tracker Extension

- Extension for [Ulauncher](https://github.com/Ulauncher/Ulauncher/) heavily inspired by [Flow Toggl Plugin](https://github.com/JamesNZL/flow-toggl-plugin).

## Requirements & Installation

### Pre Requisites

1. [Ulauncher](https://github.com/Ulauncher/Ulauncher/) with 2.0 API
2. Tested on Python 3.10, 3.11, 3.12

### Installation

1. Install through Ulauncher GUI
2. Setup your authentication. It checks in order of:
    1. Ulauncher Config Api Token
    2. Environment Variables
        - Either **TOGGL_API_TOKEN** or if using email **TOGGL_API_TOKEN** + **TOGGL_PASSWORD**
    3. *.togglrc* in the default home location. Configuration from [Toggl CLI](https://github.com/AuHau/toggl-cli).
3. Set your default workspace inside the configuration and anything else you would like to customize.
4. You're now ready to use the extension.

> [!NOTE]
> This will install [Toggl Api Wrapper](https://pypi.org/project/toggl-api-wrapper/) on startup and update the dependency if needed. If you run into issues please check out your root pip installation and double check the wrapper is present with `/usr/bin/pip list | grep toggl`


## Usage
- Invoked in Ulauncher with the `tgl` prefix by default.
- Check out the [usage guide](docs/guide.md) for more details.
- Use `tgl help <command>` inside the extension to get more details on a specific command.

### Supports
- **Trackers**
    1. Continuing a tracker.
    2. Stopping a tracker.
    3. Editing a tracker.
    4. Starting a new tracker.
    5. Adding a new tracker.
    6. Deleting a tracker.
    8. Listing all trackers.
- **Projects**
    1. Listing your projects.
    2. Adding projects.
    3. Editing projects.
    4. Deleting projects.
- **Clients**
    1. Listing your clients.
    2. Adding clients.
    3. Editing clients.
    4. Deleting clients.
- **Tags**
    1. Listing your tags.
    2. Adding tags.
    3. Editing tags.
    4. Deleting tags.

# License

MIT. Look at the [LICENSE](LICENSE.md) for details.
