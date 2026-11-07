# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from abc import ABC, abstractmethod


class NodeListBatch(ABC):
    def __init__(self, existing, items, properties):
        self.existing = existing
        self.items = items
        self.properties = properties

    @cached_property
    def paths(self):
        return self.get_paths()

    def get_paths(self):
        return [item['path'] for item in self.existing if item and item.get('path')]

    @cached_property
    def result(self):
        return self.get_result()

    @abstractmethod
    def get_result(self):
        pass


class NodeListAddition(NodeListBatch):
    def get_item(self, item):
        item.update(self.properties)
        return item

    def get_result(self):
        return [self.get_item(item) for item in self.items if item and item['path'] not in self.paths]


class NodeListDeletion(NodeListBatch):
    def get_paths(self):
        return [item['path'] for item in self.items if item and item.get('path')]

    def matches(self, item):
        if not item or item.get('path') not in self.paths:
            return False
        return all(key in item and item[key] == value for key, value in self.properties.items())

    def get_result(self):
        paths = self.paths
        return [index for index, item in enumerate(self.existing) if self.matches(item)]
