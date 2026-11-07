# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property


class MenuLookup:
    def __init__(self, lookup, skin, menu, item=None, node=None, mode=None, guid=None, **kwargs):
        self.lookup = lookup
        self.skin = skin
        self.menu = menu
        self.item = item
        self.node = node
        self.mode = mode
        self.guid = guid
        self.filters = {key[7:]: value for key, value in kwargs.items() if key.startswith('filter_')}

    @cached_property
    def directory(self):
        return self.get_directory()

    def get_directory(self):
        from resources.lib.shortcuts.node.controller import ListGetShortcutsNode
        directory = ListGetShortcutsNode(None, None)
        directory.refresh = True
        directory.skin = self.skin
        directory.menu = self.menu
        directory.item = self.item
        directory.node = self.node
        directory.mode = self.mode
        directory.guid = self.guid
        directory.edit = False
        return directory

    def matches(self, item):
        return all(key in item and item[key] == value for key, value in self.filters.items())

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        if not self.directory.menunode:
            return ''
        items = (item if isinstance(item, dict) else {'value': item} for item in self.directory.menunode)
        item = next((item for item in items if self.matches(item) and item), None)
        return (item.get(self.lookup) or '') if item else ''


def get_menunode_lookup(lookup, skin, menu, item=None, node=None, mode=None, guid=None, **kwargs):
    return MenuLookup(lookup, skin, menu, item, node, mode, guid, **kwargs).result
