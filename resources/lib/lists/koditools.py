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
