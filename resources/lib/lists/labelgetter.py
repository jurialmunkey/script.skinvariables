# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmc import getInfoLabel
from xbmcgui import ListItem
from jurialmunkey.ftools import cached_property


class ListInfoLabelGetter:

    listitem_key = None

    def __init__(self, container_id, listitem_pos=None):
        self.container_id = container_id
        self.listitem_pos = listitem_pos

    @property
    def container(self):
        if self.container_id is None:
            return ''
        if self.container_id == 0:
            return 'Container.'
        return f'Container({self.container_id}).'

    @property
    def listitem(self):
        if self.listitem_key is None:
            return ''
        if self.listitem_pos is None:
            return f'{self.listitem_key}.'
        return f'{self.listitem_key}({self.listitem_pos}).'

    def get_infolabel(self, infolabel):
        return getInfoLabel(f'{self.container}{self.listitem}{infolabel}')


class ListItemAbsoluteInfoLabelGetter(ListInfoLabelGetter):
    listitem_key = 'ListItemAbsolute'


class ListGetListLabelsItems:

    def __init__(self, container, infolabel, **infoprops):
        self.container = container
        self.infolabel = infolabel
        self.infoprops = infoprops

    @cached_property
    def numitems(self):
        return int(ListInfoLabelGetter(self.container).get_infolabel('NumItems') or 0)

    @cached_property
    def allitems(self):
        return tuple((self.get_listitem(x) for x in range(self.numitems)))

    def get_listitem(self, x):
        listitem = ListItem(
            label=ListItemAbsoluteInfoLabelGetter(self.container, x).get_infolabel(self.infolabel),
            label2='',
            path='',
            offscreen=True
        )
        listitem.setProperties({
            ip: ListItemAbsoluteInfoLabelGetter(self.container, x).get_infolabel(il)
            for il, ip in self.infoprops.items()
        })

        return listitem
