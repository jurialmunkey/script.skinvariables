# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from resources.lib.settingsearch.kodisettings import KodiSettingChange


class NoCloseAction:
    """Stands in for a close action when the settings search closes without one."""

    def run(self):
        pass


class SettingNavigation:
    """Opens a settings window with focus on a setting or category once the settings search has closed.

    Kodi refuses to open windows while a modal dialog is open so the settings search closes before this runs.
    """

    # Settings window that briefly replaces the target window when the target is already open.
    replacement_window = 'Settings'

    def __init__(self, window, target):
        self.window = window
        self.target = target

    @property
    def is_window_active(self):
        return xbmc.getCondVisibility(f'Window.IsActive({self.window})')

    def run(self):
        # Kodi ignores the focus target when the window is already active, such as the settings window under the
        # settings search, so another window replaces it first and the target window opens again from there.
        if self.is_window_active:
            xbmc.executebuiltin(f'ReplaceWindow({self.replacement_window})', True)
        xbmc.executebuiltin(f'ActivateWindow({self.window},{self.target})', True)


class ReloadingSettingChange(KodiSettingChange):
    """Change to a setting that makes Kodi reload the skin, which deletes script dialogs.

    The settings search closes first and the change runs once it has closed.
    """

    def apply(self, window):
        window.close_with(self)


def get_setting_change(setting, value):
    change_class = ReloadingSettingChange if setting.is_reloading else KodiSettingChange
    return change_class(setting.key, value)
