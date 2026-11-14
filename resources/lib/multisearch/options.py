# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property


class SearchOptions:
    """Filter values and sort method when a search is submitted. Sources that look them up use them in their paths.

    The values are copied so changing the filters later does not change a search that is waiting or running.
    """

    def __init__(self, filters, sort_method):
        self.values = filters.values
        self.sort_method = sort_method

    @cached_property
    def key(self):
        """Hashable options for the results cache of the sources."""
        return self.get_key()

    def get_key(self):
        return (*sorted(self.values.items()), self.sort_method.__name__)
