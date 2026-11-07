# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property


FILTER_KEYNAMES = (
    'filter_key',
    'filter_value',
    'filter_operator',
    'filter_empty',
    'exclude_key',
    'exclude_value',
    'exclude_operator',
)


class FilterParameters:
    def __init__(self, params, prefix=None):
        self.params = params
        self.prefix = prefix

    def get_key_group(self, key):
        name, separator, group = key.partition('__')
        group = group if separator else '0'
        if self.prefix:
            if not name.startswith(self.prefix):
                return
            name = name[len(self.prefix):]
        if name in FILTER_KEYNAMES:
            return (name, group)

    @cached_property
    def groups(self):
        return self.get_groups()

    def get_groups(self):
        groups = {}
        for key, value in self.params.items():
            pair = self.get_key_group(key)
            if pair is not None:
                name, group = pair
                groups.setdefault(group, {})[name] = value
        return groups


def get_filters(filter_prefix=None, **kwargs):
    return FilterParameters(kwargs, filter_prefix).groups
