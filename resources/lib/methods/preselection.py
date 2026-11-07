# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from contextlib import suppress


class DialogSelectPreselectedItems:
    empty = -1

    def __init__(self, preselected_values, list_items):
        self.preselected_values = preselected_values
        self.list_items = list_items

    def get_preselected_value(self, value):
        try:
            return int(value)
        except TypeError:
            return
        except ValueError:
            pass
        with suppress(ValueError):
            return self.list_items.index(value)

    def get_preselected_output(self):
        index = self.get_preselected_value(self.preselected_values[0])
        return self.empty if index is None else index

    @property
    def preselected_items(self):
        return self.get_preselected_items()

    def get_preselected_items(self):
        if not self.preselected_values or not self.list_items:
            return self.empty
        return self.get_preselected_output()


class DialogMultiSelectPreselectedItems(DialogSelectPreselectedItems):
    empty = (-1,)

    def get_preselected_output(self):
        indices = (self.get_preselected_value(value) for value in self.preselected_values)
        return [index for index in indices if index is not None] or self.empty
