# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import ListItem
from jurialmunkey.ftools import cached_property
from resources.lib.viewtypes.common import get_localized


class ViewTypesItem:
    def __init__(self, viewtypes, view_id, icons=None):
        self.viewtypes = viewtypes
        self.view_id = view_id
        self.icons = icons

    @cached_property
    def name(self):
        return self.get_name()

    def get_name(self):
        return get_localized(self.viewtypes.get(self.view_id))

    @cached_property
    def icon(self):
        return self.get_icon()

    def get_icon(self):
        return self.icons.get(self.view_id) if self.icons else ''

    @cached_property
    def item(self):
        return self.get_item()

    def get_item(self):
        item = ListItem(label=self.name)
        item.setArt({'thumb': self.icon, 'icon': self.icon})
        return item


class ViewTypesGroup:
    def __init__(self, key, items, icon=None):
        self.key = key
        self.items = items
        self.icon = icon or ''

    @cached_property
    def name(self):
        return self.get_name()

    def get_name(self):
        return get_localized(self.key)

    @cached_property
    def item(self):
        return self.get_item()

    def get_item(self):
        item = ListItem(label=self.name)
        item.setArt({'thumb': self.icon, 'icon': self.icon})
        return item
