# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmcgui


CLOSE_ACTIONS = (xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK)


class UnmanagedControl:
    """Stands in for skin controls that the script did not generate."""

    def onfocus(self, window):
        pass

    def onclick(self, window):
        pass


UNMANAGED_CONTROL = UnmanagedControl()


class ScriptWindowMixin:
    """Passes focus and clicks to the generated item with the control id."""

    @property
    def controls(self):
        raise NotImplementedError

    def get_item(self, control_id):
        return self.controls.get(control_id, UNMANAGED_CONTROL)

    def set_properties(self, properties):
        for name, value in properties.items():
            self.setProperty(name, value)

    def onFocus(self, control_id):
        self.get_item(control_id).onfocus(self)

    def onClick(self, control_id):
        self.get_item(control_id).onclick(self)

    def onAction(self, action):
        if action.getId() not in CLOSE_ACTIONS:
            return
        self.close()


class ScriptWindow(ScriptWindowMixin, xbmcgui.WindowXML):
    pass


class ScriptDialog(ScriptWindowMixin, xbmcgui.WindowXMLDialog):
    pass
