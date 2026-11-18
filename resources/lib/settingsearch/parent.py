# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmcgui


ACTIVE_PROPERTY = 'SkinVariables.SettingSearch.Active'


class ParentSearchState:
    """Search state that the settings search sets on the window under it.

    Skins cannot read the properties of a script dialog from another window, so the window under the dialog gets a
    property while a search or tag is active. The skin can then hide what the results show over.
    """

    def __init__(self, window_id):
        self.window = xbmcgui.Window(window_id)

    def set_active(self, is_active):
        self.window.setProperty(ACTIVE_PROPERTY, 'true' if is_active else '')

    def clear(self):
        self.set_active(False)
