# -*- coding: utf-8 -*-
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xml.etree.ElementTree as ET


"""
Module for converting xml based template config code into json
"""


class Meta():
    def __init__(self, root, meta):
        self.root = root
        self.meta = meta

    def set_listtext(self, tag, key=None):
        value = [i.text for i in self.root.findall(tag)]
        if not value:
            return
        self.meta[key or tag] = value
        return value

    def set_dicttext(self, tag, key=None):
        value = {item.attrib['name']: item.text for item in self.root.findall(tag)}
        if not value:
            return
        self.meta[key or tag] = value
        return value

    def set_itemtext(self, tag, key=None):
        value = next((i.text for i in self.root.findall(tag) if i.text), None)
        if not value:
            return
        self.meta[key or tag] = value
        return value

    def set_value(self, root):
        items = []
        name = root.attrib['name'] if 'name' in root.attrib else 'value'
        if not list(root):
            self.meta[name] = root.text
            return items
        items.append(Meta(root, self.meta.setdefault(name, {})))
        return items

    def set_rules(self, root):
        return self.set_children(root, 'rule', root.attrib['name'])

    def set_items(self, root):
        self.meta.update(root.attrib)
        return self.set_children(root, 'item', 'for_each')

    def get_child(self, root, children):
        meta = {}
        children.append(meta)
        return Meta(root, meta)

    def set_children(self, root, tag, key):
        self.meta[key] = []
        return [self.get_child(item, self.meta[key]) for item in root.findall(tag)]

    def set_lists(self, root):
        items = []
        self.meta['list'] = []
        for item in root.findall('list'):
            meta = {}
            pair = [item.attrib['name'], meta]
            self.meta['list'].append(pair)
            items.append(Meta(item, meta))
        if not items:
            del self.meta['list']
            return []
        return items


class XMLtoJSON():

    routes = {'value': 'set_value', 'items': 'set_items', 'rules': 'set_rules', 'lists': 'set_lists'}

    def __init__(self, filecontent):
        self.root = ET.fromstring(filecontent)
        self.meta = {}

    def get_meta(self):
        self.get_contents(Meta(self.root, self.meta))
        return self.meta

    def get_contents(self, meta):
        meta.set_listtext('condition')
        meta.set_itemtext('template')
        meta.set_listtext('datafile')
        meta.set_dicttext('enumitem')

        for child in self.get_children(meta):
            self.get_contents(child)

    def get_children(self, meta):
        for item in meta.root:
            method = self.routes.get(item.tag)
            if method:
                yield from getattr(meta, method)(item)


def xml_to_json(filecontent):
    return XMLtoJSON(filecontent).get_meta()
