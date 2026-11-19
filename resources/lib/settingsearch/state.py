# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.skinsettings.state import SkinSettingsViewState


class SettingSearchViewState(SkinSettingsViewState):
    """View of the newly opened settings search. It starts without a search at the given settings level."""

    def __init__(self, level):
        self.level = level

    def apply(self, window):
        window.restore_view(self.level, '', '', {})
