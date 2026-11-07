# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from jurialmunkey.jsnrpc import get_jsonrpc
from jurialmunkey.litems import ContainerDirectory
from resources.lib.lists.koditools.common import WindowProperties, clear_windowprops_decorator


class JSONRPCProperties:
    def __init__(self, method, params, properties):
        self.method = method
        self.params = params
        self.properties = properties

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        return (get_jsonrpc(self.method, self.params) or {}).get('result')

    @cached_property
    def item(self):
        return self.get_item()

    def get_item(self):
        item = ContainerDirectory.get_list_item(self.method)
        for key, value in self.result.items():
            item[1].setProperty(str(key), str(value))
            self.properties.set(key, value)
        self.properties.store_keys(self.result)
        return item


class ListGetJSONRPC(ContainerDirectory):
    @clear_windowprops_decorator
    def get_directory(self, info, method, window_prop=None, window_id=None, **kwargs):
        result = JSONRPCProperties(method, kwargs, WindowProperties(window_prop, window_id))
        if not result.result:
            return
        self.add_items([result.item])
        return result.result
