# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import ListItem
from infotagger.listitem import ListItemInfoTag
from jurialmunkey.litems import ContainerDirectory
from jurialmunkey.ftools import cached_property
from jurialmunkey.parser import boolean
from resources.lib.lists.labelgetter import ListGetListLabelsItems


class ListGetQuickStatsItems:
    limit = 0
    separator = ' / '
    remove_unknown = True

    def __init__(self, items):
        self.items = items

    @property
    def total(self):
        return len({item for lst in self.unique_items.values() for item in lst})

    def get_count(self, k):
        return len(self.unique_items[k])

    def get_percent(self, k):
        return int(self.get_count(k) / self.total * 100)

    @cached_property
    def unique_labels(self):
        unique_labels = {sub for itm in self.items for sub in itm.getLabel().split(self.separator)}
        unique_labels = sorted(unique_labels)
        return unique_labels

    def get_unique_items(self):
        return {
            label: tuple((
                item for item in self.items
                if label in item.getLabel().split(self.separator)
            ))
            for label in self.unique_labels
        }

    @cached_property
    def unique_items(self):
        unique_items = self.get_unique_items()
        unique_items = {k: v for k, v in unique_items.items() if k and v} if self.remove_unknown else unique_items
        return self.get_limit(unique_items, self.limit) if self.limit else unique_items

    def get_limit(self, items, amount):
        return dict(sorted(items.items(), key=lambda kv: len(kv[1]), reverse=True)[:amount])

    @cached_property
    def allitems(self):
        return tuple((self.get_listitem(k, v) for k, v in self.unique_items.items()))

    def get_listitem(self, k, v):
        listitem = ListItem(label=k, offscreen=True)
        listitem.setProperty('count', str(self.get_count(k)))
        listitem.setProperty('total', str(self.total))
        listitem.setProperty('percent', str(self.get_percent(k)))
        listitem.setLabel2(f'{listitem.getProperty("percent")}%')
        ListItemInfoTag(listitem, 'video').set_info({'year': listitem.getProperty('count')})
        return listitem


class ListGetQuickStatsRangeItems(ListGetQuickStatsItems):

    def __init__(self, items, divisor=10):
        self.items = items
        self.divisor = int(divisor)

    def get_division(self, item):
        try:
            return str(int(int(item.getLabel()) / self.divisor) * self.divisor)
        except (ValueError, TypeError):
            return ''

    @cached_property
    def unique_divisions(self):
        unique_divisions = {self.get_division(item) for item in self.items}
        unique_divisions = sorted(unique_divisions)
        return unique_divisions

    def get_unique_items(self):
        return {
            division: tuple((
                item for item in self.items
                if division == self.get_division(item)
            ))
            for division in self.unique_divisions
        }


class ListGetQuickStats(ContainerDirectory):

    def get_directory(self, containers, infolabel, divisor=None, limit=None, remove_unknown=True, **kwargs):
        items = [
            listitem for container in containers.split()
            for listitem in ListGetListLabelsItems(container, infolabel).allitems
        ]
        items = ListGetQuickStatsRangeItems(items, divisor) if divisor else ListGetQuickStatsItems(items)
        items.limit = int(limit) if limit else 0
        items.remove_unknown = boolean(remove_unknown)
        self.add_items([('', listitem, True, ) for listitem in items.allitems])
