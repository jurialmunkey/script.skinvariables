# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from math import isfinite
from jurialmunkey.ftools import cached_property
from jurialmunkey.parser import boolean
from resources.lib.lists.labelgetter import ListGetListLabelsItems
from resources.lib.lists.quickstats import ListGetQuickStats, ListGetQuickStatsItems, ListGetQuickStatsRangeItems


class ListGetStackedBarStatsItems(ListGetQuickStatsItems):
    sort_by = None
    other = True
    minimum = 0
    infovalue = None

    def get_value(self, item):
        if not self.infovalue:
            return 1
        try:
            value = float(item.getProperty(self.infovalue))
        except (ValueError, TypeError):
            return 0
        if not isfinite(value) or value < 0:
            return 0
        return int(value) if value.is_integer() else value

    @cached_property
    def item_values(self):
        return {item: self.get_value(item) for item in self.items}

    def get_items_count(self, items):
        count = sum(self.item_values[item] for item in items)
        return int(count) if isinstance(count, float) and count.is_integer() else count

    @property
    def total(self):
        return self.get_items_count({item for lst in self.unique_items.values() for item in lst})

    def get_count(self, k):
        return self.get_items_count(self.unique_items[k])

    def get_limit(self, items, amount):
        return dict(sorted(items.items(), key=lambda kv: self.get_items_count(kv[1]), reverse=True)[:amount])

    @cached_property
    def unique_items(self):
        unique_items = self.get_unique_items()
        unique_items = {k: v for k, v in unique_items.items() if k and v} if self.remove_unknown else unique_items
        if self.limit <= 0 and self.minimum <= 0:
            return unique_items

        limited_items = self.get_limit(unique_items, self.limit) if self.limit > 0 else unique_items
        total = sum(self.get_items_count(v) for v in limited_items.values())
        limited_items = {k: v for k, v in limited_items.items() if self.get_items_count(v) * 100 >= self.minimum * total}
        if not self.other:
            return limited_items
        other = tuple((
            item for k, v in unique_items.items()
            if k not in limited_items
            for item in v
        ))
        if other:
            limited_items['other'] = limited_items.get('other', ()) + other
        return limited_items

    @cached_property
    def ranked_items(self):
        return self.get_limit(self.unique_items, len(self.unique_items))

    def get_sort_value(self, items):
        return items[0].getProperty(self.sort_by) if self.sort_by and items else ''

    @cached_property
    def sorted_items(self):
        if not self.sort_by:
            return self.ranked_items
        return dict(sorted(self.unique_items.items(), key=lambda kv: self.get_sort_value(kv[1])))

    @cached_property
    def segment_counts(self):
        total = sum(self.get_count(k) for k in self.ranked_items)
        if not total:
            return {k: 0 for k in self.ranked_items}

        # Normalize label memberships so overlapping labels still fill one bar.
        divisions = {k: divmod(self.get_count(k) * 100, total) for k in self.ranked_items}
        counts = {k: int(v[0]) for k, v in divisions.items()}
        remainder = 100 - sum(counts.values())
        for k in sorted(divisions, key=lambda k: divisions[k][1], reverse=True)[:remainder]:
            counts[k] += 1
        return counts

    @cached_property
    def allitems(self):
        return tuple((
            self.get_listitem(k, v, x)
            for k, v in self.sorted_items.items()
            for x in range(self.segment_counts[k])
        ))

    def get_listitem(self, k, v, x):
        listitem = super().get_listitem(k, v)
        listitem.setProperty('rank', str(tuple(self.ranked_items).index(k) + 1))
        listitem.setProperty('sort_by', self.get_sort_value(v))
        position = str(tuple(self.sorted_items).index(k) + 1)
        if x == 0:
            listitem.setProperty('segment_start', position)
        if x == (self.segment_counts[k] - 1) // 2:
            listitem.setProperty('segment_center', position)
        if x == self.segment_counts[k] - 1:
            listitem.setProperty('segment_end', position)
        return listitem


class ListGetStackedBarStatsRangeItems(ListGetQuickStatsRangeItems, ListGetStackedBarStatsItems):
    pass


class ListGetStackedBarStats(ListGetQuickStats):
    items_class = ListGetStackedBarStatsItems
    range_items_class = ListGetStackedBarStatsRangeItems

    def get_directory(self, containers, infolabel, divisor=None, limit=None, remove_unknown=True, sort_by=None, other=True, min=None, infovalue=None, **kwargs):
        infoprops = {il: il for il in (infovalue, sort_by) if il}
        items = [
            listitem for container in containers.split()
            for listitem in ListGetListLabelsItems(container, infolabel, **infoprops).allitems
        ]
        items = self.range_items_class(items, divisor) if divisor else self.items_class(items)
        items.limit = int(limit) if limit else 0
        items.minimum = float(min) if min else 0
        items.remove_unknown = boolean(remove_unknown)
        items.sort_by = sort_by
        items.other = boolean(other)
        items.infovalue = infovalue
        self.add_items([('', listitem, True, ) for listitem in items.allitems])
