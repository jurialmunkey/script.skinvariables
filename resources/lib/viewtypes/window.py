# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xml.etree.ElementTree as ET
import xbmcvfs
from jurialmunkey.ftools import cached_property
from resources.lib.scriptwindow.controller import ScriptWindowController, ScriptWindowFile
from resources.lib.scriptwindow.template import ScriptWindowTemplate
from resources.lib.scriptwindow.window import ScriptDialog
from resources.lib.viewtypes.preview import FOCUSED_LIST_ID, PREVIEW_LIMIT, ViewTypesPreviews
from resources.lib.viewtypes.windowitems import VIEWID_PROPERTY


class ViewTypesPreviewList:
    """Skin list with the id of a viewtype. Shown while that viewtype is focused and filled with preview items.

    The optional limit attribute sets how many items the list gets. Defaults to PREVIEW_LIMIT.
    """

    def __init__(self, view_id, control):
        self.view_id = view_id
        self.control = control

    @cached_property
    def limit(self):
        return self.get_limit()

    def get_limit(self):
        return int(self.control.element.get('limit', PREVIEW_LIMIT))

    @cached_property
    def condition(self):
        return f'String.IsEqual(Window.Property({VIEWID_PROPERTY}),{self.view_id})'

    def configure(self):
        """Add a visible condition. Kodi combines it with other visible tags and ignores the limit attribute."""
        self.control.element.append(self.control.get_override_element('visible', self.condition, {}))


class ViewTypesWindowTemplate(ScriptWindowTemplate):
    """Builds the viewtype selector dialog from a skin template file written for the script."""

    filename = 'script-skinvariables-viewtypes.xml'
    list_id = '3'
    template_ids = {
        'view': '8',
        'group': '10',
        'label': '14',
    }
    # The label template is only needed for groups that are always expanded.
    default_ids = ('8', '10', '14')

    def __init__(self, folder, layout, viewtype_ids=()):
        super().__init__(folder)
        self.layout = layout
        self.viewtype_ids = viewtype_ids

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

    @cached_property
    def preview_lists(self):
        return self.get_preview_lists()

    def get_preview_lists(self):
        """Lists for every viewtype so lists for viewtypes not offered for the content stay hidden."""
        return [
            ViewTypesPreviewList(view_id, self.controls[view_id])
            for view_id in self.viewtype_ids
            if view_id in self.controls
        ]

    @cached_property
    def offered_view_ids(self):
        return self.get_offered_view_ids()

    def get_offered_view_ids(self):
        return {view.view_id for view in self.layout.views}

    @cached_property
    def preview_limits(self):
        """Item limits by viewtype for the lists of the viewtypes offered for the content."""
        return self.get_preview_limits()

    def get_preview_limits(self):
        return {
            preview_list.view_id: preview_list.limit
            for preview_list in self.preview_lists
            if preview_list.view_id in self.offered_view_ids
        }

    def configure_preview_lists(self):
        for preview_list in self.preview_lists:
            preview_list.configure()

    @cached_property
    def has_focused_list(self):
        """Whether the skin has the always visible list for the focused item."""
        return self.get_has_focused_list()

    def get_has_focused_list(self):
        return FOCUSED_LIST_ID in self.controls

    def get_document(self):
        elements = self.elements
        self.remove_default_elements()
        self.set_default_control()
        self.configure_preview_lists()
        self.controls[self.list_id].element.extend(elements)
        return self.root


class ViewTypesWindowFile(ScriptWindowFile):
    basefolder = 'special://profile/addon_data/script.skinvariables/viewtypes/'
    filename = 'script-skinvariables-viewtypes-generated.xml'

    def __init__(self, folder, layout, viewtype_ids=()):
        super().__init__(folder)
        self.layout = layout
        self.viewtype_ids = viewtype_ids

    def get_template(self):
        return ViewTypesWindowTemplate(self.folder, self.layout, self.viewtype_ids)


class ViewTypesDialog(ScriptDialog):
    def __init__(self, *args, layout=None, previews=None, preview_properties=None, **kwargs):
        self.layout = layout
        self.previews = previews
        self.preview_properties = preview_properties
        self.choice = None
        # Set before the dialog opens so the current group is expanded when Kodi focuses the default control.
        self.set_properties(self.properties)

    @property
    def properties(self):
        return {**self.layout.properties, **self.preview_properties}

    @property
    def controls(self):
        return self.layout.controls

    def fill_previews(self):
        for view_id, listitems in self.previews.items():
            self.getControl(int(view_id)).addItems(list(listitems))

    def onInit(self):
        self.fill_previews()
        self.set_properties(self.properties)
        self.setFocusId(self.layout.focus_item.control_id)

    def toggle_group(self, group):
        self.layout.group_state.toggle(self, group)

    def select(self, view):
        self.choice = view.source
        self.close()


class ViewTypesWindowController(ScriptWindowController):
    window_file_class = ViewTypesWindowFile
    window_class = ViewTypesDialog

    def __init__(self, layout, viewtype_ids=()):
        self.layout = layout
        self.viewtype_ids = viewtype_ids

    @cached_property
    def available(self):
        """Whether every skin folder has a template for the dialog."""
        return self.get_available()

    def get_available(self):
        return all(xbmcvfs.exists(ViewTypesWindowTemplate.get_filepath(folder)) for folder in self.folders)

    def get_window_file(self, folder):
        return ViewTypesWindowFile(folder, self.layout, self.viewtype_ids)

    @cached_property
    def preview_limits(self):
        """Item limits by viewtype for the preview lists of every skin folder."""
        return self.get_preview_limits()

    def get_preview_limits(self):
        return {
            view_id: limit
            for window_file in self.window_files
            for view_id, limit in window_file.template.preview_limits.items()
        }

    @cached_property
    def has_focused_list(self):
        return self.get_has_focused_list()

    def get_has_focused_list(self):
        return any(window_file.template.has_focused_list for window_file in self.window_files)

    @cached_property
    def preview(self):
        """Preview items read from the underlying window before the dialog opens."""
        return self.get_preview()

    def get_preview(self):
        return ViewTypesPreviews(self.preview_limits, self.has_focused_list)

    def get_window_kwargs(self):
        return {
            'layout': self.layout,
            'previews': self.preview.previews,
            'preview_properties': self.preview.properties,
        }

    def get_result(self, window):
        return window.choice
