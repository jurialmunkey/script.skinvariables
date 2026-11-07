# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from itertools import product
from xbmc import getInfoLabel
from jurialmunkey.ftools import cached_property
from jurialmunkey.litems import ContainerDirectory


class DottedPropertyItem:
    def __init__(self, source, x, y):
        self.source = source
        self.x = x
        self.y = y

    @cached_property
    def values(self):
        return self.get_values()

    def get_values(self):
        values = {}
        for key in self.source.keys:
            value = self.source.get_value(self.x, self.y, key)
            if value:
                values[key] = value
        return values

    @cached_property
    def label(self):
        return self.get_label()

    def get_label(self):
        return self.values.get(self.source.label_key, '')

    @cached_property
    def artwork(self):
        return self.get_artwork()

    def get_artwork(self):
        artwork = {}
        for key, value in self.values.items():
            if key == self.source.thumb_key:
                artwork['thumb'] = artwork['icon'] = value
            if key == self.source.fanart_key:
                artwork['fanart'] = value
        return artwork

    @cached_property
    def properties(self):
        return self.get_properties()

    def get_properties(self):
        return dict(self.values, xpos=str(self.x), ypos=str(self.y))

    @cached_property
    def item(self):
        return self.get_item()

    def get_item(self):
        item = ContainerDirectory.get_list_item(self.label)
        item[1].setProperties(self.properties)
        item[1].setArt(self.artwork)
        return item


class DottedProperties:
    def __init__(self, source, string, keys, label, thumb, fanart, separator, xmax, ymax, no_label_dupes):
        self.source = source
        self.string = string
        self.keys = keys.split(separator) or ['']
        self.label_key = label
        self.thumb_key = thumb
        self.fanart_key = fanart
        self.xmax = int(xmax or 1)
        self.ymax = int(ymax or 0) or 1
        self.no_label_dupes = no_label_dupes

    def get_value(self, x, y, key):
        template = f'{self.source}.Property({self.string}{{k}})'
        return getInfoLabel(template.format(x=x, y=y, k=key))

    @cached_property
    def candidates(self):
        return self.get_candidates()

    def get_candidates(self):
        candidates = (DottedPropertyItem(self, x, y) for x, y in product(range(self.xmax), range(self.ymax)))
        return [item for item in candidates if item.values]

    @cached_property
    def unique_candidates(self):
        return self.get_unique_candidates()

    def get_unique_candidates(self):
        items = {}
        for item in self.candidates:
            items.setdefault(item.label, item)
        return list(items.values())

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        candidates = self.unique_candidates if self.no_label_dupes else self.candidates
        return [item.item for item in candidates]


class ListGetDottedProperties(ContainerDirectory):
    def get_directory(
        self,
        source='Container.ListItem',
        string='',
        infoproperties='',
        label='',
        thumb=None,
        fanart=None,
        separator='/',
        xmax='10',
        ymax=None,
        no_label_dupes=False,
        **kwargs,
    ):
        if not source or not string or not xmax:
            return
        result = DottedProperties(
            source,
            string,
            infoproperties,
            label,
            thumb,
            fanart,
            separator,
            xmax,
            ymax,
            no_label_dupes,
        )
        self.add_items(result.items)
