# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmcgui
from resources.lib.skinsettings.items import DefinitionItem, CATEGORY_PROPERTY
from resources.lib.skinsettings.search import SettingsSearch, SettingsViewBounds


DESCRIPTION_CONTROL_ID = 6
CLOSE_ACTIONS = (xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK)


class UnmanagedControl(DefinitionItem):
    """Stands in for skin controls that are not part of the definition."""

    def __init__(self):
        super().__init__('', {}, 0)

    def onfocus(self, window):
        pass


UNMANAGED_CONTROL = UnmanagedControl()


class SkinSettingsWindow(xbmcgui.WindowXML):
    def __init__(self, *args, definition=None, **kwargs):
        self.definition = definition

    def get_item(self, control_id):
        return self.definition.controls.get(control_id, UNMANAGED_CONTROL)

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

    def set_properties(self, properties):
        for name, value in properties.items():
            self.setProperty(name, value)

    def set_search(self, query):
        self.set_properties(SettingsSearch(query, self.definition.groups, self.definition.settings).properties)

    def set_view_bounds(self):
        self.set_properties(SettingsViewBounds(self.definition.ordered_settings).properties)

    def onFocus(self, control_id):
        self.get_item(control_id).onfocus(self)

    def onClick(self, control_id):
        # Clicks change the search text or skin settings that the settings visibility can depend on.
        self.get_item(control_id).onclick(self)
        self.definition.search.onchangeview(self)

    def onAction(self, action):
        if action.getId() not in CLOSE_ACTIONS:
            return
        self.close()
