# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from copy import deepcopy
from xbmcgui import Dialog, ListItem
from jurialmunkey.ftools import cached_property
from resources.lib.kodiutils import get_localized
from resources.lib.shortcuts.node.constants import ICON_ADD, ICON_WIDGET
from resources.lib.shortcuts.node.context import FormatDict, get_contextmenu


class SubmenuSelection:
    def __init__(self, directory, mode):
        self.directory = directory
        self.mode = mode

    @cached_property
    def node(self):
        return self.get_node()

    def get_node(self):
        return '.'.join([str(index) for index in self.directory.node] + [str(self.directory.item)])

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        from resources.lib.shortcuts.node.controller import ListGetShortcutsNode
        directory = self.directory
        submenu = ListGetShortcutsNode(directory.handle, directory.paramstring, **directory.params)
        return submenu.get_directory(
            menu=directory.menu,
            skin=directory.skin,
            node=self.node,
            mode=self.mode,
            func='list',
        )

    def get_choice(self, entry):
        item = entry[1]
        item.setLabel2(entry[0])
        icon = item.getArt('icon') or item.getArt('thumb') or ICON_WIDGET
        item.setArt({'icon': icon, 'thumb': icon})
        return item

    def get_add_choice(self):
        item = ListItem(label=f'{get_localized(32078)}...')
        item.setArt({'icon': ICON_ADD, 'thumb': ICON_ADD})
        return item

    @cached_property
    def choices(self):
        return self.get_choices()

    def get_choices(self):
        return [self.get_choice(entry) for entry in self.items] + [self.get_add_choice()]

    @cached_property
    def contextmenu(self):
        return self.get_contextmenu()

    def get_contextmenu(self):
        return get_contextmenu(self.node, self.mode)

    def select_action(self, index):
        if index == len(self.items):
            return 0
        item = self.choices[index]
        mapping = FormatDict({'label': item.getLabel(), 'listitem_obj': item})
        labels = [label.format_map(mapping) for label, *_ in self.contextmenu]
        return Dialog().select(item.getLabel(), list=labels)

    def apply(self, index, action):
        from resources.lib.shortcuts.node.controller import ListGetShortcutsNode
        params = deepcopy(self.directory.params)
        params['paths'] = self.contextmenu[action][2]
        submenu = ListGetShortcutsNode(-1, '', **params)
        submenu.get_directory(
            menu=self.directory.menu,
            skin=self.directory.skin,
            node=self.node,
            mode=self.mode,
            item=index,
            func=self.contextmenu[action][1],
        )

    def process(self):
        index = Dialog().select(get_localized(1034), list=self.choices, useDetails=True)
        if index == -1:
            return False
        contextmenu = self.contextmenu
        action = self.select_action(index)
        if action != -1:
            self.apply(index, action)
        return True


class SubmenuDialog:
    def __init__(self, directory, mode):
        self.directory = directory
        self.mode = mode

    def run(self):
        while SubmenuSelection(self.directory, self.mode).process():
            pass
