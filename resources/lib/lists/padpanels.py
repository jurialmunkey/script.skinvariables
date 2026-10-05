# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmc import getInfoLabel
from xbmcgui import ListItem
from jurialmunkey.litems import ContainerDirectory
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


class ListGetPanelPaddedItems:

    def __init__(self, items, rows=None):
        self.items = items
        self.rows = rows or 7

    def get_padded_column(self, items, rows):
        padded_column = [ListItem(label='', label2='', path='', offscreen=True)] * ((-len(items)) % rows)
        padded_column = [self.finalise_listitem(i, x) for x, i in enumerate(items)] + padded_column
        return padded_column

    def finalise_listitem(self, li, x):
        li.setProperty('group_start', 'True') if x == 0 else None
        li.setProperty('currentitem', f'{x + 1}')
        li.setProperty('position', f'{x % self.rows + 1}')
        return li

    @cached_property
    def columns(self):
        return {
            label: [itm for itm in self.items if itm.getLabel() == label]
            for label in list(dict.fromkeys((i.getLabel() for i in self.items)))
        }

    @cached_property
    def padded_columns(self):
        return {
            k: self.get_padded_column(v, self.rows)
            for k, v in self.columns.items()
        }

    @cached_property
    def paditems(self):
        return tuple((i for v in self.padded_columns.values() for i in v))


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


class ListGetPanelLabels(ContainerDirectory):

    def get_directory(self, containers, infoproperties, infolabel, length, **kwargs):

        from resources.lib.method import get_paramstring_tuplepairs
        infoprops = dict(get_paramstring_tuplepairs(infoproperties))

        items = [
            i for container in containers.split()
            for i in ListGetListLabelsItems(container, infolabel, **infoprops).allitems
        ]

        self.add_items([
            ('', listitem, True, )
            for listitem in ListGetPanelPaddedItems(items, int(length)).paditems
        ])
