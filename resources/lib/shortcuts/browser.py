# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import ListItem, Dialog


SHORTCUT_CONFIG = 'skinvariables-shortcut-config.json'
SHORTCUT_FOLDER = 'special://skin/shortcuts/'
TARGET_NODE_BLOCKLIST = ['link', None]


class GetDirectoryBrowser():
    def __init__(self, return_item=False, use_details=True, item_prefix=None):
        self.history = []
        self.filepath = f'{SHORTCUT_FOLDER}{SHORTCUT_CONFIG}'
        self.item_prefix = item_prefix or ''
        self.return_item = return_item
        self.use_details = use_details

    @property
    def definitions(self):
        try:
            return self._definitions
        except AttributeError:
            from resources.lib.shortcuts.futils import read_meta_from_file
            self._definitions = read_meta_from_file(self.filepath)
            return self._definitions

    def get_onclick_path(self, path, node=None):
        if not path:
            return
        if not node:
            return f'PlayMedia({path})'
        if node == 'link':
            return f'{path}'
        return f'ActivateWindow({node},{path},return)'

    def get_new_item(self, item):
        # Update to new item values
        icon = item[1].getArt('thumb') or ''
        node = item[1].getProperty('nodetype') or None
        name = item[1].getProperty('nodename') or item[1].getLabel() or ''
        path = item[0] or ''

        if item[2]:  # Item is a folder so we open it
            return self.get_directory(path, icon, name, item, True)

        if not self.return_item:  # Just want action not full item
            return self.get_onclick_path(path, node)

        return {
            "label": name,
            "path": path,
            "icon": icon,
            "target": node if node not in TARGET_NODE_BLOCKLIST else '',
        }

    def get_items(self, directory, path, icon, name, item, add_item=False):
        directory_items = directory.items.copy()

        if add_item and path and not path.startswith('grouping://'):
            li = ListItem(label='Add folder...', label2=path, path=path, offscreen=True)
            li.setArt({'icon': icon, 'thumb': icon})
            li.setProperty('nodename', name)
            li.setProperty('nodetype', item[1].getProperty('nodetype') or '')
            directory_items.insert(0, (path, li, False, ))

        items = [i[1] for i in directory_items if i]
        x = Dialog().select(heading=name or path, list=items, useDetails=self.use_details)
        if x != -1:
            item = directory_items[x]
            self.history.append((directory, path, icon, name, item, True, )) if item[2] else None  # Add old values to history before updating
            return self.get_new_item(item)
        try:
            return self.get_items(*self.history.pop())
        except IndexError:
            return []

    def get_directory(self, path='grouping://shortcuts/', icon='', name='Shortcuts', item=None, add_item=False):
        if not path:
            return

        from resources.lib.shortcuts.grouping import GetDirectoryGrouping
        DirectoryClass = GetDirectoryGrouping

        if not path.startswith('grouping://'):
            from resources.lib.shortcuts.jsonrpc import GetDirectoryJSONRPC
            DirectoryClass = GetDirectoryJSONRPC

        directory = DirectoryClass(path, definitions=self.definitions, target=item[1].getProperty('nodetype') if item else None)
        if not directory.items:
            return

        if not item:
            li = ListItem(label=name, label2=path, path=path, offscreen=True)
            li.setArt({'icon': icon, 'thumb': icon})
            li.setProperty('nodename', name)
            item = (path, li, True, )

        return self.get_items(directory, path, icon, name, item, add_item)
