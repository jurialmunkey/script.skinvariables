# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmcgui
from jurialmunkey.ftools import cached_property
from resources.lib.scriptwindow.window import ScriptDialog
from resources.lib.settingsearch.closeactions import NoCloseAction
from resources.lib.settingsearch.kodisettings import KodiSettingValues
from resources.lib.settingsearch.parent import ParentSearchState
from resources.lib.settingsearch.search import SettingSearchMatches
from resources.lib.settingsearch.state import SettingSearchReloadedViewState
from resources.lib.skinsettings.window import SettingsWindowMixin


class SettingSearchDialog(SettingsWindowMixin, ScriptDialog):
    """Dialog that lists the settings matching the search under their "Window > Category" headings.

    It can open over a settings window. Kodi settings change in place. Settings that a script cannot change, and
    settings that reload the skin, close it so the controller can open their settings window or change them.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Settings level the search shows settings up to. Set by the view state when the dialog initialises.
        self.level = None
        # Action the controller runs after the dialog closes, such as opening a settings window.
        self.close_action = NoCloseAction()
        # Set when a slider changes a setting so the other settings are read again once focus leaves it.
        self.refresh_pending = False

    def get_window_id(self):
        return xbmcgui.getCurrentWindowDialogId()

    @cached_property
    def parent_state(self):
        """Search state set on the window under the dialog. Read on first use while this dialog is open."""
        return self.get_parent_state()

    def get_parent_state(self):
        # Kodi does not count dialogs as windows so the current window is the one under the dialog.
        return ParentSearchState(xbmcgui.getCurrentWindowId())

    def update_search(self):
        super().update_search()
        self.parent_state.set_active(self.settings_search.is_active)

    def close(self):
        self.parent_state.clear()
        super().close()

    def set_level(self, level):
        self.level = level
        self.set_properties(level.properties)

    @property
    def settings_search(self):
        return SettingSearchMatches(
            self.search_query,
            self.search_tag,
            self.level,
            self.definition.headings,
            self.definition.settings,
        )

    @property
    def view_settings(self):
        # Only matching settings show so the view bounds only check those.
        return sorted(self.settings_search.matched_settings, key=lambda setting: setting.order)

    def restore_view(self, level, query, tag, properties):
        self.set_properties(properties)
        self.set_level(level)
        self.restore_search(query, tag)

    def get_reload_state(self, focus_id):
        return SettingSearchReloadedViewState(
            self.level,
            self.search_query,
            self.search_tag,
            self.definition.search.get_state_properties(self),
            focus_id,
        )

    def close_with(self, close_action):
        """Close so the controller can run the action once no modal dialog is open."""
        self.close_action = close_action
        self.close()

    def refresh_kodi_settings(self):
        settings = KodiSettingValues().settings
        for setting in self.definition.kodi_settings:
            setting.set_value(self, settings.get(setting.key))

    def refresh_after_change(self):
        """Read the settings again because a change can change other values, options and enabled states."""
        self.refresh_pending = False
        self.refresh_kodi_settings()
        self.update_search()

    def onFocus(self, control_id):
        if self.refresh_pending:
            self.refresh_after_change()
        super().onFocus(control_id)

    def onInit(self):
        # The dialog id is read while this dialog is on top, before other dialogs such as the keyboard open over it.
        self.window_id
        self.refresh_kodi_settings()
        super().onInit()
