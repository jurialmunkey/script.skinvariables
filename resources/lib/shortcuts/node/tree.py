# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
import random
from jurialmunkey.parser import parse_localize


def get_default_item():
    return {'label': '', 'icon': '', 'path': '', 'target': '', 'submenu': [], 'widgets': []}


def get_submenunode(meta, mode='submenu'):
    try:
        return meta[mode]
    except KeyError:
        meta[mode] = []
        return meta[mode]


def get_submenuitem(meta, n):
    try:
        return meta[n]
    except IndexError:
        meta.append(get_default_item())
        return meta[-1]


def get_menuguid(meta, guid, mode='submenu', subkeys=('submenu', 'widgets')):
    return MenuGuidLookup(meta, guid, mode, subkeys).result


def get_menunode(meta, node, mode='submenu'):
    """ Lookup menu node using node value and return tuple of meta for item and current node """
    if not meta or not node:  # Return base of meta if no node because were in main menu
        return (meta, node, '')

    for n in node[:-1]:  # Walk submenus until last item
        meta = get_submenuitem(meta, n)
        meta = get_submenunode(meta)

    for n in node[-1:]:  # Last item we get in the current mode
        meta = get_submenuitem(meta, n)
        name = parse_localize(meta.get('label', ''))
        meta = get_submenunode(meta, mode)

    return (meta, node, name)


def get_nodename(node):
    return '.'.join([f'{n}' for n in node])


def get_menunode_item(menunode, x):
    try:
        return menunode[x]
    except IndexError:
        menunode.append(get_default_item())
        return menunode[x]


def assign_guid(meta):
    return MenuIdentifiers(meta).result


class MenuIdentifiers:
    def __init__(self, meta):
        self.meta = meta
        self.identifiers = []

    def get_unique_guid(self, guid=None):
        guid = guid or f'guid-{random.randrange(16**8):08x}'
        while guid in self.identifiers:
            guid = f'guid-{random.randrange(16**8):08x}'
        return guid

    def assign_item(self, item):
        item['guid'] = self.get_unique_guid(item.get('guid'))
        self.identifiers.append(item['guid'])
        self.assign_children(item, 'submenu')
        self.assign_children(item, 'widgets')

    def assign_children(self, item, key):
        if key in item:
            self.assign_items(item[key])

    def assign_items(self, items):
        for item in items:
            self.assign_item(item)

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        if self.meta:
            self.assign_items(self.meta)
        return self.meta


class MenuGuidLookup:
    def __init__(self, meta, guid, mode, subkeys):
        self.meta = meta
        self.guid = guid
        self.mode = mode
        self.subkeys = subkeys

    def get_item(self, item, node):
        name = parse_localize(item.get('label', ''))
        if item.get('guid') == self.guid:
            return get_submenunode(item, self.mode), node, name
        for key in self.subkeys:
            child, child_node, child_name = self.get_items(item.get(key) or [])
            if isinstance(child, list):
                return child, child_node + node, child_name
        return None, None, None

    def get_items(self, menu):
        for index, item in enumerate(menu):
            match = self.get_item(item, [index])
            if isinstance(match[0], list):
                return match
        return None, None, None

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        if not self.meta or not self.guid:
            return
        item, node, name = self.get_items(self.meta)
        return item, tuple(node) if node else (), name
