# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.method import set_to_windowprop
from jurialmunkey.litems import Container


class ListGetNumberSum(Container):
    def get_directory(self, expression, window_prop=None, window_id=None, **kwargs):

        values = [0]
        values += [int(i) for i in expression.split() if i]

        label = f'{sum(values)}'
        items = [self.get_list_item(label)]
        set_to_windowprop(label, 0, window_prop, window_id)

        self.add_items(items)


class ListGetSplitString(Container):
    def get_directory(self, values=None, infolabel=None, separator='|', window_prop=None, window_id=None, **kwargs):
        from xbmc import getInfoLabel as get_infolabel
        values = get_infolabel(infolabel) if infolabel else values

        if not values:
            return

        x = 0
        items = []
        for i in values.split(separator):
            if not i:
                continue
            label = f'{i}'
            items.append(self.get_list_item(label))
            set_to_windowprop(label, x, window_prop, window_id)
            x += 1

        self.add_items(items)


class ListGetEncodedString(Container):
    def get_directory(self, paths=None, window_prop=None, window_id=None, **kwargs):
        from urllib.parse import quote_plus

        if not paths:
            return

        items = []
        for x, i in enumerate(paths):
            label = quote_plus(i)
            items.append(self.get_list_item(label))
            set_to_windowprop(label, x, window_prop, window_id)

        self.add_items(items)


class ListGetFileExists(Container):
    def get_directory(self, paths, window_prop=None, window_id=None, **kwargs):
        import xbmcvfs

        if not paths:
            return

        items = []
        for x, i in enumerate(paths):
            label = i
            path = i if xbmcvfs.exists(i) else ''
            items.append(self.get_list_item(label))
            set_to_windowprop(path, x, window_prop, window_id)

        self.add_items(items)
