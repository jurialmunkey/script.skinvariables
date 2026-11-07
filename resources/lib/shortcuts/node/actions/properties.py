# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import Dialog
from jurialmunkey.ftools import cached_property
from jurialmunkey.parser import parse_localize


class PropertyEdit:
    def __init__(self, item, key, heading, choices):
        self.item = item
        self.key = key
        self.heading = heading
        self.choices = choices

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        pairs = (item.partition('=') for item in self.choices.split('&') if item)
        return [(key, value if separator else key) for key, separator, value in pairs]

    @cached_property
    def preselect(self):
        return self.get_preselect()

    def get_preselect(self):
        current = self.item.get(self.key)
        return next((index for index, item in enumerate(self.items) if item[1] == current), -1)

    def select(self):
        index = Dialog().select(heading=self.heading, list=[item[0] for item in self.items], preselect=self.preselect)
        if index == -1:
            return -1
        value = self.items[index][1]
        return None if value == 'edit' else value

    def input(self):
        return Dialog().input(heading=self.heading, defaultt=parse_localize(self.item.get(self.key) or ''))
