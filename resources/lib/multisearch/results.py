# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.filterdir.items import FilterDirItems
from resources.lib.filterdir.paths import FilterDirPaths


class SearchResult:
    """Directory item from a search source with the source details the skin uses to style it."""

    def __init__(self, source, rank, item):
        self.source = source
        self.rank = rank
        self.item = item

    @cached_property
    def properties(self):
        return self.get_properties()

    def get_properties(self):
        return {
            'widget_style': self.source.widget_style,
            'widget_target': self.source.target,
            'widget_icon': self.source.icon,
            'widget_rank': str(self.rank + 1),
        }

    @property
    def listitem(self):
        """New listitem each time because the list is refilled whenever the results or sort order change."""
        return self.get_listitem()

    def get_listitem(self):
        listitem = self.item.listitem
        listitem.setProperties(self.properties)
        return listitem

    def get_sort_value(self, key):
        value = self.item.infolabels.get(key) or ''
        try:
            return (1, float(value))
        except ValueError:
            return (0, str(value).lower())

    @cached_property
    def builtin(self):
        return self.get_builtin()

    def get_builtin(self):
        if self.item.is_folder:
            return f'ActivateWindow({self.source.target},"{self.item.path}",return)'
        return f'PlayMedia("{self.item.path}")'


class SourceResults:
    """Items of one search source for one query, limited to the results limit."""

    def __init__(self, source, query, limit):
        self.source = source
        self.query = query
        self.limit = limit

    @cached_property
    def path(self):
        return self.get_path()

    def get_path(self):
        return self.query.format(self.source.template)

    @cached_property
    def directory(self):
        return self.get_directory()

    def get_directory(self):
        paths = FilterDirPaths((self.path,), (self.source.label,))
        return FilterDirItems(paths, library=self.source.library)

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        return [
            SearchResult(self.source, rank, item)
            for rank, item in enumerate(self.directory.items[:self.limit])
        ]
