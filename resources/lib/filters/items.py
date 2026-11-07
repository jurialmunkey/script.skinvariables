# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.filters.rules import IncludeRule, ExcludeRule


class ItemFilter:
    def __init__(
        self,
        item,
        filter_key=None,
        filter_value=None,
        filter_operator=None,
        filter_empty=None,
        exclude_key=None,
        exclude_value=None,
        exclude_operator=None,
    ):
        self.item = item
        self.filter_key = filter_key
        self.filter_value = filter_value
        self.filter_operator = filter_operator
        self.filter_empty = filter_empty
        self.exclude_key = exclude_key
        self.exclude_value = exclude_value
        self.exclude_operator = exclude_operator

    @cached_property
    def metadata(self):
        return self.get_metadata()

    def get_metadata(self):
        return (self.item.get('infolabels', {}), self.item.get('infoproperties', {}))

    @cached_property
    def include(self):
        return self.get_include()

    def get_include(self):
        return IncludeRule(self.metadata, self.filter_key, self.filter_value, self.filter_operator, self.filter_empty)

    @cached_property
    def exclude(self):
        return self.get_exclude()

    def get_exclude(self):
        return ExcludeRule(self.metadata, self.exclude_key, self.exclude_value, self.exclude_operator)

    @cached_property
    def excluded(self):
        return self.get_excluded()

    def get_excluded(self):
        if not self.item:
            return
        if self.include.excluded or self.exclude.excluded:
            return True


def is_excluded(
    item,
    filter_key=None,
    filter_value=None,
    filter_operator=None,
    filter_empty=None,
    exclude_key=None,
    exclude_value=None,
    exclude_operator=None,
):
    return ItemFilter(
        item,
        filter_key,
        filter_value,
        filter_operator,
        filter_empty,
        exclude_key,
        exclude_value,
        exclude_operator,
    ).excluded
