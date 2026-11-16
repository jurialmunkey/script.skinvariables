# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmcgui
from jurialmunkey.ftools import cached_property
from resources.lib.scriptwindow.window import ScriptWindow
from resources.lib.skinsettings.items import CATEGORY_PROPERTY
from resources.lib.skinsettings.search import SettingsSearch, SettingsTags, SettingsViewBounds


DESCRIPTION_CONTROL_ID = 6


class SkinSettingsWindow(ScriptWindow):
    def __init__(self, *args, definition=None, **kwargs):
        self.definition = definition
        self.search_query = ''
        self.search_tag = ''

    @property
    def controls(self):
        return self.definition.controls

    def set_description(self, text):
        self.getControl(DESCRIPTION_CONTROL_ID).setText(text)

    def set_category(self, key):
        # Returning focus to the selected category is not a change so it keeps the search text.
        if self.getProperty(CATEGORY_PROPERTY) == key:
            return
        self.setProperty(CATEGORY_PROPERTY, key)
        self.definition.search.onchangecategory(self)
        self.definition.search.onchangeview(self)

    def get_text(self, control_id):
        return self.getControl(control_id).getText()

    def set_text(self, control_id, text):
        self.getControl(control_id).setText(text)

    def get_slider_value(self, control_id):
        return self.getControl(control_id).getInt()

    def set_slider_value(self, control_id, value, maximum):
        self.getControl(control_id).setInt(value, 0, 1, maximum)

    def refresh_settings(self):
        for setting in self.definition.settings:
            setting.onrefresh(self)

    @property
    def settings_search(self):
        return SettingsSearch(self.search_query, self.search_tag, self.definition.groups, self.definition.settings)

    def update_search(self):
        self.set_properties(self.settings_search.properties)

    def set_search(self, query):
        self.search_query = query
        self.update_search()

    def set_tag(self, tag):
        self.search_tag = tag
        self.update_search()

    def clear_search(self):
        self.search_query = ''
        self.search_tag = ''
        self.update_search()

    def choose_tag(self, heading):
        # Selecting the search view first lets the tags reflect the settings that the search shows.
        self.definition.search.onchoosetag(self)
        tags = SettingsTags(self.settings_search, self.window_id)
        position = xbmcgui.Dialog().select(heading, tags.labels, preselect=tags.preselect)
        if position == -1:
            return
        self.set_tag(tags.get_tag(position))

    @cached_property
    def window_id(self):
        """Id of this window. Read on first use when this window is active, which dialogs over it do not change."""
        return self.get_window_id()

    def get_window_id(self):
        return xbmcgui.getCurrentWindowId()

    def set_view_bounds(self):
        self.set_properties(SettingsViewBounds(self.definition.ordered_settings, self.window_id).properties)

    def onInit(self):
        self.refresh_settings()

    def onFocus(self, control_id):
        # Settings can change while a dialog opened by a click is shown so moving focus also refreshes the view.
        super().onFocus(control_id)
        self.refresh_settings()
        self.definition.search.onchangeview(self)

    def onClick(self, control_id):
        # Clicks change the search text or skin settings that the settings visibility can depend on.
        super().onClick(control_id)
        self.definition.search.onchangeview(self)
