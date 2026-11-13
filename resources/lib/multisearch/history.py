# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmcgui
from jurialmunkey.ftools import cached_property
from resources.lib.multisearch.constants import PROPERTY_PREFIX


HOME_WINDOW_ID = 10000


class StoredQuery:
    """Search text of a shortcuts menu kept on the Home window, so it is only restored in the current Kodi session."""

    def __init__(self, menu):
        self.menu = menu

    @cached_property
    def window(self):
        return xbmcgui.Window(HOME_WINDOW_ID)

    @cached_property
    def property_name(self):
        return f'{PROPERTY_PREFIX}.{self.menu}.Query'

    @property
    def value(self):
        return self.window.getProperty(self.property_name)

    def set_value(self, text):
        self.window.setProperty(self.property_name, text)
