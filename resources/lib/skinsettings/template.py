# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xml.etree.ElementTree as ET
import xbmcvfs
from copy import deepcopy
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import load_filecontent
from resources.lib.xmlhelper.serializer import XML_HEADER


class TemplateControl:
    """Control in a skin template, written as a <control> or as an <include> that passes the control id as a param."""

    def __init__(self, element):
        self.element = element

    @property
    def control_id(self):
        raise NotImplementedError

    def set_control_id(self, control_id):
        raise NotImplementedError

    def clone(self):
        return type(self)(deepcopy(self.element))

    @staticmethod
    def get_override_element(tag, text, attrib):
        element = ET.Element(tag, attrib)
        element.text = text
        return element

    def configure(self, control_id, overrides):
        """Replace the template tags given by overrides. Includes receive them as nested content."""
        tags = {tag for tag, text, attrib in overrides}
        for child in [child for child in self.element if child.tag in tags]:
            self.element.remove(child)
        self.element.extend(self.get_override_element(*override) for override in overrides)
        self.set_control_id(control_id)
        return self.element


class ElementControl(TemplateControl):
    @property
    def control_id(self):
        return self.element.get('id')

    def set_control_id(self, control_id):
        self.element.set('id', str(control_id))


class IncludeControl(TemplateControl):
    @cached_property
    def id_param(self):
        return self.get_id_param()

    def get_id_param(self):
        return next((param for param in self.element.findall('param') if param.get('name') == 'id'), None)

    @property
    def control_id(self):
        return self.id_param.get('value', self.id_param.text) if self.id_param is not None else None

    def set_control_id(self, control_id):
        if 'value' in self.id_param.attrib:
            self.id_param.set('value', str(control_id))
            return
        self.id_param.text = str(control_id)


TEMPLATE_CONTROL_CLASSES = {
    'control': ElementControl,
    'include': IncludeControl,
}


class SkinSettingsTemplate:
    """Builds the scripted window from a skin template file written for the script."""

    filename = 'script-skinvariables-skinsettings.xml'
    category_list_id = '3'
    settings_list_id = '5'
    template_ids = {
        'category': '10',
        'group': '14',
        'button': '7',
        'radiobutton': '8',
        'edit': '12',
    }
    # Kodi hides its default template controls in native settings windows so the script removes them.
    default_ids = ('7', '8', '9', '10', '11', '12', '13', '14', '15')

    def __init__(self, folder, definition):
        self.folder = folder
        self.definition = definition

    @classmethod
    def get_filepath(cls, folder):
        return f'special://skin/{folder}/{cls.filename}'

    @cached_property
    def filepath(self):
        return self.get_filepath(self.folder)

    @cached_property
    def root(self):
        return self.get_root()

    def get_root(self):
        return ET.fromstring(str(load_filecontent(self.filepath)))

    @cached_property
    def parents(self):
        return self.get_parents()

    def get_parents(self):
        return {child: parent for parent in self.root.iter() for child in parent}

    @cached_property
    def controls(self):
        """Template controls by id. The first control in the document wins when ids repeat."""
        return self.get_controls()

    def get_controls(self):
        controls = [
            TEMPLATE_CONTROL_CLASSES[element.tag](element)
            for element in self.root.iter()
            if element.tag in TEMPLATE_CONTROL_CLASSES
        ]
        return {control.control_id: control for control in reversed(controls) if control.control_id}

    def get_template(self, name):
        # Looked up on use so skins only need the templates for the controls a definition uses.
        return self.controls[self.template_ids[name]]

    def get_element(self, item):
        return self.get_template(item.template).clone().configure(item.control_id, item.overrides)

    @cached_property
    def category_elements(self):
        return self.get_category_elements()

    def get_category_elements(self):
        return [self.get_element(category) for category in self.definition.categories]

    @cached_property
    def settings_elements(self):
        return self.get_settings_elements()

    def get_settings_elements(self):
        return [self.get_element(item) for item in self.definition.layout]

    @cached_property
    def default_elements(self):
        return self.get_default_elements()

    @cached_property
    def placed_ids(self):
        """Template controls that stay where the skin placed them and are configured in place."""
        return self.get_placed_ids()

    def get_placed_ids(self):
        return {self.template_ids[item.template] for item in self.definition.search.placed_items}

    def get_default_elements(self):
        return [
            self.controls[control_id].element
            for control_id in self.default_ids
            if control_id in self.controls and control_id not in self.placed_ids
        ]

    def configure_placed_items(self):
        for item in self.definition.search.placed_items:
            self.get_template(item.template).configure(item.control_id, item.overrides)

    @cached_property
    def document(self):
        return self.get_document()

    def get_document(self):
        category_elements, settings_elements = self.category_elements, self.settings_elements
        for element in self.default_elements:
            self.parents[element].remove(element)
        self.configure_placed_items()
        self.controls[self.category_list_id].element.extend(category_elements)
        self.controls[self.settings_list_id].element.extend(settings_elements)
        return self.root

    @cached_property
    def text(self):
        return self.get_text()

    def get_text(self):
        return '\n'.join((XML_HEADER, ET.tostring(self.document, encoding='unicode')))


class SettingsCategoryTemplate(SkinSettingsTemplate):
    """Builds the scripted window from the skin's SettingsCategory.xml when the skin has no script template."""

    filename = 'SettingsCategory.xml'


def get_skinsettings_template(folder, definition):
    exists = xbmcvfs.exists(SkinSettingsTemplate.get_filepath(folder))
    template_class = SkinSettingsTemplate if exists else SettingsCategoryTemplate
    return template_class(folder, definition)
