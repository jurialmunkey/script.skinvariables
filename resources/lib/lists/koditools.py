# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import ListItem
from resources.lib.container import Container


class ListGetNumberSum(Container):
    def get_directory(self, expression, **kwargs):

        values = [0]
        values += [int(i) for i in expression.split() if i]

        items = [{
            'url': '',
            'listitem': ListItem(label=f'{sum(values)}', label2='', path='', offscreen=True),
            'isFolder': True}]

        self.add_items(items)


class ListGetSplitString(Container):
    def get_directory(self, values=None, infolabel=None, separator='|', **kwargs):
        from xbmc import getInfoLabel as get_infolabel
        values = get_infolabel(infolabel) if infolabel else values

        if not values:
            return

        items = [{
            'url': '',
            'listitem': ListItem(label=f'{i}', label2='', path='', offscreen=True),
            'isFolder': True} for i in values.split(separator) if i]

        self.add_items(items)
