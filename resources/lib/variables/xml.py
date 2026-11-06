# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xml.etree.ElementTree as ET
from json import dumps
from jurialmunkey.ftools import cached_property
from jurialmunkey.parser import try_int, del_empty_keys


class XMLVariable:
    content_key = 'values'

    def __init__(self, root):
        self.root = root

    @cached_property
    def content(self):
        return self.get_content()

    def get_content(self):
        return [{item.attrib.get('condition') or 'True': item.text} for item in self.root]

    def get_container_range(self, value):
        if '...' not in value:
            return (int(value),)
        return range(*(int(part) + index for index, part in enumerate(value.split('...'))))

    @cached_property
    def containers(self):
        return self.get_containers()

    def get_containers(self):
        return [
            container
            for value in self.root.attrib.get('containers', '').split(',')
            for container in self.get_container_range(value)
        ]

    @cached_property
    def meta(self):
        return self.get_meta()

    def get_meta(self):
        attributes = self.root.attrib
        meta = {
            self.content_key: self.content,
            'name': attributes['name'],
            'containers': self.containers,
            'listitems': {'start': try_int(attributes.get('start')), 'end': try_int(attributes.get('end'))},
            'types': attributes['types'].split(',') if attributes.get('types') else ['listitem'],
            'parent': attributes.get('parent'),
            'null_id': attributes.get('null_id'),
        }
        return del_empty_keys(meta)


class XMLExpression(XMLVariable):
    content_key = 'expression'

    def get_content(self):
        return self.root.text


class XMLVariables:
    definition_classes = {'variable': XMLVariable, 'expression': XMLExpression}

    def __init__(self, source):
        self.root = ET.fromstring(source)

    @cached_property
    def definitions(self):
        return self.get_definitions()

    def get_definitions(self):
        return [
            self.definition_classes[root.tag](root)
            for root in self.root
            if root.attrib.get('name') and root.tag in self.definition_classes
        ]

    @cached_property
    def meta(self):
        return self.get_meta()

    def get_meta(self):
        return [definition.meta for definition in self.definitions if definition.content]

    @cached_property
    def content(self):
        return self.get_content()

    def get_content(self):
        return dumps(self.meta)
