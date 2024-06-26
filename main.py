from ulauncher_toggl_extension.utils import ensure_import

ensure_import("toggl_api", "toggl-api-wrapper", "0.3.0")

from ulauncher_toggl_extension.extension import TogglExtension  # noqa: E402

if __name__ == "__main__":
    TogglExtension().run()
