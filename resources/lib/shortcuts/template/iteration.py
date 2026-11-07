# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from copy import deepcopy
from abc import ABC, abstractmethod
from jurialmunkey.ftools import cached_property
from resources.lib.shortcuts.node.controller import ListGetShortcutsNode


class TemplateIteration(ABC):
    def __init__(self, part):
        self.part = part
        self.actions = part.genxml.pop('for_each')

    @property
    def scopes(self):
        return self.get_scopes()

    @abstractmethod
    def get_scopes(self):
        pass

    def get_action_params(self, scope, action_index):
        return scope

    @cached_property
    def contents(self):
        return self.get_contents()

    def get_contents(self):
        return [
            content
            for scope in self.scopes
            for action_index, action in enumerate(self.actions)
            for content in self.part.get_contents(action, self.get_action_params(scope, action_index))
        ]


class ListIteration(TemplateIteration):
    def __init__(self, part):
        self.items = part.genxml.pop('list')
        super().__init__(part)

    def get_scope(self, item, definitions):
        params = deepcopy(self.part.params)
        params.update(definitions)
        params.update({f'parent_{key}': value for key, value in params.items()})
        params['item'] = item
        return params

    def get_scopes(self):
        return (self.get_scope(item, definitions) for item, definitions in self.items)


class MenuIteration(TemplateIteration):
    def __init__(self, part):
        super().__init__(part)
        self.menu = part.get_formatted(part.genxml.pop('menu', ''))
        self.item = part.get_formatted(part.genxml.pop('item', ''))
        self.mode = part.get_formatted(part.genxml.pop('mode', ''))

    @cached_property
    def nodes(self):
        return self.get_nodes()

    def get_nodes(self):
        directory = ListGetShortcutsNode(None, None)
        directory.refresh = True
        return directory.get_directory(
            menu=self.menu,
            skin=self.part.skinid,
            node=self.item,
            mode=self.mode,
            func='node',
        ) or []

    def get_scope(self, index, item):
        item = {'value': item} if isinstance(item, str) else item
        item.pop('submenu', [])
        item.pop('widgets', [])
        return index, item

    def get_scopes(self):
        return (self.get_scope(index, item) for index, item in enumerate(self.nodes))

    def get_action_params(self, scope, action_index):
        index, item = scope
        params = deepcopy(self.part.params)
        params.update({f'parent_{key}': value for key, value in params.items()})
        params.update({f'item_{key}': value for key, value in item.items()})
        params.update(
            item_x=index,
            item_action_x=action_index,
            item_length_x=len(self.nodes),
            item_menu=self.menu,
            item_node=self.item,
            item_mode=self.mode,
        )
        return params
