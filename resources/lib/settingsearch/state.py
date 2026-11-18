# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.skinsettings.state import SkinSettingsViewState


class SettingSearchViewState(SkinSettingsViewState):
    """View of the newly opened settings search. It starts without a search at the given settings level."""

    def __init__(self, level):
        self.level = level

    def apply(self, window):
        window.restore_view(self.level, '', '', {})


class SettingSearchReloadedViewState(SettingSearchViewState):
    """View saved before the skin reloads. The reopened settings search shows it again with focus on the setting."""

    def __init__(self, level, query, tag, properties, focus_id):
        super().__init__(level)
        self.query = query
        self.tag = tag
        self.properties = properties
        self.focus_id = focus_id

    def apply(self, window):
        window.restore_view(self.level, self.query, self.tag, self.properties)
        window.setFocusId(self.focus_id)
