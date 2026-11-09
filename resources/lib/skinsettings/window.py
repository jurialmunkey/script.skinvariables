# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmcgui
from resources.lib.skinsettings.items import DefinitionItem, CATEGORY_PROPERTY
from resources.lib.skinsettings.search import SettingsSearch


DESCRIPTION_CONTROL_ID = 6
CLOSE_ACTIONS = (xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK)
STEP_ACTIONS = {
    xbmcgui.ACTION_MOVE_LEFT: -1,
    xbmcgui.ACTION_MOVE_RIGHT: 1,
}


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

    def get_text(self, control_id):
        return self.getControl(control_id).getText()

    def set_text(self, control_id, text):
        self.getControl(control_id).setText(text)

    def set_search(self, query):
        search = SettingsSearch(query, self.definition.groups, self.definition.settings)
        for name, value in search.properties.items():
            self.setProperty(name, value)

    def set_slider(self, control_id, value, maximum):
        """Position a plain slider provided by the skin template. Other control types show the value in label2."""
        try:
            control = self.getControl(control_id)
        except RuntimeError:  # Kodi raises for control types that python cannot access such as sliderex.
            return
        if not isinstance(control, xbmcgui.ControlSlider):
            return
        control.setInt(value, 0, 1, maximum)

    def onInit(self):
        for setting in self.definition.settings:
            setting.oninit(self)

    def onFocus(self, control_id):
        self.get_item(control_id).onfocus(self)

    def onClick(self, control_id):
        self.get_item(control_id).onclick(self)

    def onAction(self, action):
        action_id = action.getId()
        if action_id in CLOSE_ACTIONS:
            self.close()
            return
        if action_id not in STEP_ACTIONS:
            return
        self.get_item(self.getFocusId()).onstep(self, STEP_ACTIONS[action_id])
