# -*- coding: utf-8 -*-
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.filters.items import ItemFilter
from resources.lib.filters.parameters import FILTER_KEYNAMES, FilterParameters


__all__ = ('FILTER_KEYNAMES', 'get_filters', 'is_excluded')


def get_filters(filter_prefix=None, **kwargs):
    return FilterParameters(kwargs, filter_prefix).groups


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
