# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import re
import xml.etree.ElementTree as ET
from copy import deepcopy
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import load_filecontent
from resources.lib.xmlhelper.serializer import XML_HEADER


SUBSTITUTION_PATTERN = re.compile(r'\$SUBSTITUTE\[(\w+)\]')


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

    @staticmethod
    def get_substituted_text(text, substitutions):
        return SUBSTITUTION_PATTERN.sub(lambda match: substitutions[match.group(1)], text)

    def substitute(self, substitutions):
        """Replace $SUBSTITUTE[name] in the template text with the item's string value for name."""
        for element in [element for element in self.element.iter() if element.text]:
            element.text = self.get_substituted_text(element.text, substitutions)

    @property
    def tags(self):
        return {child.tag for child in self.element}

    def get_missing_defaults(self, defaults):
        tags = self.tags
        return [default for default in defaults if default[0] not in tags]

    def remove_tags(self, tags):
        for child in [child for child in self.element if child.tag in tags]:
            self.element.remove(child)

    def configure(self, item):
        """Configure the template for the item. Includes receive the overrides and defaults as nested content."""
        self.substitute(item.substitutions)
        defaults = self.get_missing_defaults(item.defaults)
        self.remove_tags({tag for tag, text, attrib in item.overrides})
        self.element.extend(self.get_override_element(*override) for override in item.overrides + defaults)
        self.set_control_id(item.control_id)
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


class ScriptWindowTemplate:
    """Builds a scripted window from a skin template file by cloning its template controls into the window."""

    filename = ''
    template_ids = {}
    # Template controls that are only sources for clones and are removed from the window.
    default_ids = ()

    def __init__(self, folder):
        self.folder = folder

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
        # Looked up on use so skins only need the templates for the controls they use.
        return self.controls[self.template_ids[name]]

    def get_element(self, item):
        return self.get_template(item.template).clone().configure(item)

    @cached_property
    def placed_ids(self):
        """Template controls that stay where the skin placed them and are configured in place."""
        return self.get_placed_ids()

    def get_placed_ids(self):
        return set()

    @cached_property
    def default_elements(self):
        return self.get_default_elements()

    def get_default_elements(self):
        return [
            self.controls[control_id].element
            for control_id in self.default_ids
            if control_id in self.controls and control_id not in self.placed_ids
        ]

    def remove_default_elements(self):
        for element in self.default_elements:
            self.parents[element].remove(element)

    @cached_property
    def document(self):
        return self.get_document()

    def get_document(self):
        raise NotImplementedError

    @cached_property
    def text(self):
        return self.get_text()

    def get_text(self):
        return '\n'.join((XML_HEADER, ET.tostring(self.document, encoding='unicode')))
