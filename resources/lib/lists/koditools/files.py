# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmcvfs
from jurialmunkey.ftools import cached_property
from jurialmunkey.litems import ContainerDirectory
from resources.lib.lists.koditools.common import WindowProperties, clear_windowprops_decorator
from resources.lib.lists.koditools.scripts import ScriptContainerDirectory


class FileExistsItem:
    def __init__(self, path, index, properties):
        self.path = path
        self.index = index
        self.properties = properties

    @cached_property
    def item(self):
        return self.get_item()

    @cached_property
    def value(self):
        return self.get_value()

    def get_value(self):
        return self.path if xbmcvfs.exists(self.path) else ''

    def get_item(self):
        item = ContainerDirectory.get_list_item(self.path)
        self.properties.set(self.index, self.value)
        return item

    @cached_property
    def script_values(self):
        return self.get_script_values()

    def get_script_values(self):
        return {'Label': self.path, 'Property(FileExists)': self.value}


class FileSizeItem:
    units = ('B', 'KB', 'MB', 'GB')

    def __init__(self, path, index, properties):
        self.path = path
        self.index = index
        self.properties = properties

    @cached_property
    def size(self):
        return self.get_size()

    def get_size(self):
        if not xbmcvfs.exists(self.path):
            return
        return xbmcvfs.Stat(self.path).st_size()

    @cached_property
    def labels(self):
        return self.get_labels()

    def get_labels(self):
        if self.size is None:
            return {}
        return {unit: f'{self.size / pow(1024, index):.2f} {unit}' for index, unit in enumerate(self.units)}

    @cached_property
    def keys(self):
        return self.get_keys()

    def get_keys(self):
        return [f'{self.index}.{unit}' for unit in self.labels]

    @cached_property
    def item(self):
        return self.get_item()

    def get_item(self):
        item = ContainerDirectory.get_list_item(self.path)
        for unit, label in self.labels.items():
            item[1].setProperty(f'FileSize.{unit}', label)
            self.properties.set(f'{self.index}.{unit}', label)
        return item

    @cached_property
    def script_values(self):
        return self.get_script_values()

    def get_script_values(self):
        return {'Label': self.path, **{f'Property(FileSize.{unit})': label for unit, label in self.labels.items()}}


class ListGetFileExists(ScriptContainerDirectory):
    @clear_windowprops_decorator
    def get_directory(self, paths, window_prop=None, window_id=None, **kwargs):
        if not paths:
            return
        properties = WindowProperties(window_prop, window_id)
        files = [FileExistsItem(path, index, properties) for index, path in enumerate(paths)]
        items = [file.item for file in files]
        properties.store_count(len(items))
        self.add_items(items)
        self.run_item_script([file.script_values for file in files])


class ListGetFileSize(ScriptContainerDirectory):
    @clear_windowprops_decorator
    def get_directory(self, paths, window_prop=None, window_id=None, **kwargs):
        if not paths:
            return
        properties = WindowProperties(window_prop, window_id)
        files = [FileSizeItem(path, index, properties) for index, path in enumerate(paths)]
        items = [file.item for file in files]
        properties.store_keys(key for file in files for key in file.keys)
        self.add_items(items)
        self.run_item_script([file.script_values for file in files])
