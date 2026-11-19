# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from urllib.parse import quote_plus
from xbmc import getInfoLabel
from jurialmunkey.ftools import cached_property
from jurialmunkey.litems import ContainerDirectory
from resources.lib.lists.koditools.common import WindowProperties, clear_windowprops_decorator
from resources.lib.lists.koditools.scripts import ScriptContainerDirectory


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

    @cached_property
    def labels(self):
        return self.get_labels()

    def get_labels(self):
        return [self.get_label(value) for value in self.values]

    def get_item(self, index, label):
        item = ContainerDirectory.get_list_item(label)
        self.properties.set(index, label)
        return item

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        return [self.get_item(index, label) for index, label in enumerate(self.labels)]

    @cached_property
    def script_values(self):
        return self.get_script_values()

    def get_script_values(self):
        return [{'Label': label} for label in self.labels]


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


class ListGetSplitString(ScriptContainerDirectory):
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
        self.run_item_script(result.script_values)


class ListGetEncodedString(ScriptContainerDirectory):
    @clear_windowprops_decorator
    def get_directory(self, paths=None, window_prop=None, window_id=None, **kwargs):
        if not paths:
            return
        properties = WindowProperties(window_prop, window_id)
        result = EncodedStringItems(paths, properties)
        items = result.items
        properties.store_count(len(items))
        self.add_items(items)
        self.run_item_script(result.script_values)
