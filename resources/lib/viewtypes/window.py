# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xml.etree.ElementTree as ET
import xbmcvfs
from jurialmunkey.ftools import cached_property
from resources.lib.scriptwindow.controller import ScriptWindowController, ScriptWindowFile
from resources.lib.scriptwindow.template import ScriptWindowTemplate
from resources.lib.scriptwindow.window import ScriptWindow


class ViewTypesWindowTemplate(ScriptWindowTemplate):
    """Builds the viewtype selector window from a skin template file written for the script."""

    filename = 'script-skinvariables-viewtypes.xml'
    list_id = '3'
    template_ids = {
        'view': '8',
        'group': '10',
    }
    default_ids = ('8', '10')

    def __init__(self, folder, layout):
        super().__init__(folder)
        self.layout = layout

    @cached_property
    def elements(self):
        return self.get_elements()

    def get_elements(self):
        return [self.get_element(item) for item in self.layout.ordered_items]

    @cached_property
    def default_control(self):
        return self.get_default_control()

    def get_default_control(self):
        element = self.root.find('defaultcontrol')
        return element if element is not None else ET.SubElement(self.root, 'defaultcontrol')

    def set_default_control(self):
        # Kodi focuses the default control after setting the initial visibility from the window properties.
        self.default_control.text = str(self.layout.focus_item.control_id)
        self.default_control.set('always', 'true')

    def get_document(self):
        elements = self.elements
        self.remove_default_elements()
        self.set_default_control()
        self.controls[self.list_id].element.extend(elements)
        return self.root


class ViewTypesWindowFile(ScriptWindowFile):
    basefolder = 'special://profile/addon_data/script.skinvariables/viewtypes/'
    filename = 'script-skinvariables-viewtypes-generated.xml'

    def __init__(self, folder, layout):
        super().__init__(folder)
        self.layout = layout

    def get_template(self):
        return ViewTypesWindowTemplate(self.folder, self.layout)


class ViewTypesWindow(ScriptWindow):
    def __init__(self, *args, layout=None, **kwargs):
        self.layout = layout
        self.choice = None
        # Set before the window opens so the current group is expanded when Kodi focuses the default control.
        self.set_properties(self.layout.properties)

    @property
    def controls(self):
        return self.layout.controls

    def onInit(self):
        self.set_properties(self.layout.properties)
        self.setFocusId(self.layout.focus_item.control_id)

    def toggle_group(self, group):
        self.layout.group_state.toggle(self, group)

    def select(self, view):
        self.choice = view.source
        self.close()


class ViewTypesWindowController(ScriptWindowController):
    window_file_class = ViewTypesWindowFile
    window_class = ViewTypesWindow

    def __init__(self, layout):
        self.layout = layout

    @cached_property
    def available(self):
        """Whether every skin folder has a template for the window."""
        return self.get_available()

    def get_available(self):
        return all(xbmcvfs.exists(ViewTypesWindowTemplate.get_filepath(folder)) for folder in self.folders)

    def get_window_file(self, folder):
        return ViewTypesWindowFile(folder, self.layout)

    def get_window_kwargs(self):
        return {'layout': self.layout}

    def get_result(self, window):
        return window.choice
