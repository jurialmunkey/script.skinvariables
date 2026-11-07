# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import ListItem
from jurialmunkey.ftools import cached_property
from resources.lib.filters.items import is_excluded
from resources.lib.lists.labelgetter import ListInfoLabelGetter, ListItemAbsoluteInfoLabelGetter


class ContainerLabelItems:
    def __init__(
        self,
        containers,
        infolabel,
        thumb=None,
        label2=None,
        separator=' / ',
        contextmenu=None,
        **filters,
    ):
        from resources.lib.params import get_paramstring_tuplepairs
        self.containers = containers.split()
        self.infolabels = infolabel.split()
        self.thumb = thumb
        self.label2 = label2
        self.separator = separator
        self.contextmenu = get_paramstring_tuplepairs(contextmenu)
        self.filters = dict(filters, filter_key='title', exclude_key='title')

    def get_position_labels(self, container, position):
        getter = ListItemAbsoluteInfoLabelGetter(container, position)
        image = getter.get_infolabel(self.thumb) if self.thumb else ''
        label = getter.get_infolabel(self.label2) if self.label2 else ''
        titles = (getter.get_infolabel(infolabel) for infolabel in self.infolabels)
        return ((title, image, label) for value in titles if value for title in value.split(self.separator))

    def get_container_labels(self, container):
        numitems = int(ListInfoLabelGetter(container).get_infolabel('NumItems') or 0)
        return (item for position in range(numitems) for item in self.get_position_labels(container, position))

    @cached_property
    def unique_labels(self):
        return self.get_unique_labels()

    def get_unique_labels(self):
        labels = (item for container in self.containers for item in self.get_container_labels(container))
        return tuple(dict.fromkeys(labels))

    @cached_property
    def labels(self):
        return self.get_labels()

    def get_labels(self):
        return tuple(item for item in self.unique_labels if not self.get_is_excluded(item[0]))

    def get_is_excluded(self, title):
        return is_excluded({'infolabels': {'title': title}}, **self.filters)

    def get_listitem(self, title, image, label):
        listitem = ListItem(label=title, label2=label or '', path='', offscreen=True)
        listitem.setArt({'icon': image or '', 'thumb': image or ''})
        values = {'label': title, 'thumb': image, 'label2': label}
        contextmenu = [(key.format(**values), value.format(**values)) for key, value in self.contextmenu]
        listitem.addContextMenuItems(contextmenu)
        return ('', listitem, True)

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        return [self.get_listitem(*item) for item in self.labels]
