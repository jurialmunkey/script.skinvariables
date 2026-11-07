# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.litems import ContainerDirectory
from jurialmunkey.window import get_property
from resources.lib.lists.koditools.common import WindowProperties, clear_windowprops_decorator


class ListGetRefreshCounter(ContainerDirectory):
    @clear_windowprops_decorator
    def get_directory(self, uid, window_prop=None, window_id=None, **kwargs):
        value = int(get_property(uid, prefix='SkinVariables') or 0) + 1
        get_property(uid, prefix='SkinVariables', set_property=str(value))
        label = str(value)
        items = [self.get_list_item(label)]
        WindowProperties(window_prop, window_id).set(0, label)
        self.add_items(items)


class ListGetNumberSum(ContainerDirectory):
    @clear_windowprops_decorator
    def get_directory(self, expression, window_prop=None, window_id=None, **kwargs):
        label = str(sum(int(value) for value in expression.split() if value))
        items = [self.get_list_item(label)]
        WindowProperties(window_prop, window_id).set(0, label)
        self.add_items(items)
