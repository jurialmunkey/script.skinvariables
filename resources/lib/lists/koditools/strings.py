# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from urllib.parse import quote_plus
from xbmc import getInfoLabel
from jurialmunkey.ftools import cached_property
from jurialmunkey.litems import ContainerDirectory
from resources.lib.lists.koditools.common import WindowProperties, clear_windowprops_decorator


class StringItems:
    def __init__(self, source, properties):
        self.source = source
        self.properties = properties

    @cached_property
    def values(self):
        return self.get_values()

    def get_values(self):
        raise NotImplementedError

    def get_label(self, value):
        return value

    def get_item(self, index, value):
        label = self.get_label(value)
        item = ContainerDirectory.get_list_item(label)
        self.properties.set(index, label)
        return item

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        return [self.get_item(index, value) for index, value in enumerate(self.values)]


class SplitStringItems(StringItems):
    def __init__(self, source, properties, separator='|'):
        super().__init__(source, properties)
        self.separator = separator

    def get_values(self):
        return [value for value in self.source.split(self.separator) if value]


class EncodedStringItems(StringItems):
    def get_values(self):
        return self.source

    def get_label(self, value):
        return quote_plus(value)


class ListGetSplitString(ContainerDirectory):
    @clear_windowprops_decorator
    def get_directory(self, values=None, infolabel=None, separator='|', window_prop=None, window_id=None, **kwargs):
        values = getInfoLabel(infolabel) if infolabel else values
        if not values:
            return
        properties = WindowProperties(window_prop, window_id)
        result = SplitStringItems(values, properties, separator)
        items = result.items
        properties.store_count(len(items))
        self.add_items(items)


class ListGetEncodedString(ContainerDirectory):
    @clear_windowprops_decorator
    def get_directory(self, paths=None, window_prop=None, window_id=None, **kwargs):
        if not paths:
            return
        properties = WindowProperties(window_prop, window_id)
        result = EncodedStringItems(paths, properties)
        items = result.items
        properties.store_count(len(items))
        self.add_items(items)
