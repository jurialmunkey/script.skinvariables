# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.filterdir.items import FilterDirItems
from resources.lib.filterdir.paths import FilterDirPaths


UNIQUE_INFOLABELS = (
    'mediatype',
    'title',
    'tvshowtitle',
    'season',
    'episode',
)


UNIQUE_ID_TYPES = {
    'tmdb': ('tmdb',),
    'imdb': ('imdb', 'imdbnumber'),
}


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
    def unique_key(self):
        """Results with the same key are the same item from the same plugin or library.

        The key is the origin, content type, title, show, season, episode and unique id. Results without uniqueids
        are only the same as themselves.
        """
        return self.get_unique_key()

    def get_unique_key(self):
        if not self.item.uniqueids:
            return self
        return (
            self.source.origin,
            *(self.item.infolabels.get(key) for key in UNIQUE_INFOLABELS),
            self.unique_id,
        )

    @cached_property
    def unique_id(self):
        """The tmdb id, otherwise the imdb id, otherwise every uniqueid when the result has neither."""
        return self.get_unique_id()

    def get_unique_id(self):
        return next(
            (
                (id_type, self.item.uniqueids[key])
                for id_type, keys in UNIQUE_ID_TYPES.items()
                for key in keys
                if self.item.uniqueids.get(key)
            ),
            frozenset(self.item.uniqueids.items()),
        )

    @cached_property
    def builtin(self):
        return self.get_builtin()

    def get_builtin(self):
        if self.item.is_folder:
            return f'ActivateWindow({self.source.target},"{self.item.path}",return)'
        return f'PlayMedia("{self.item.path}")'


class UniqueResults:
    """Results without duplicates. The first result with each unique key is kept in its original order."""

    def __init__(self, results):
        self.results = results

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        unique_results = {}
        for result in self.results:
            unique_results.setdefault(result.unique_key, result)
        return list(unique_results.values())


class CachedFilterDirItems(FilterDirItems):
    """Directory items read from the search cache when stored there, otherwise looked up and stored."""

    def __init__(self, paths, search_cache, library=None):
        super().__init__(paths, library=library)
        self.search_cache = search_cache

    def get_stored_directory(self, path):
        directory = super().get_directory(path)
        self.search_cache.set(self.library, path, directory)
        return directory

    def get_directory(self, path):
        return self.search_cache.get(self.library, path) or self.get_stored_directory(path)


class SourceResults:
    """All items of one search source for one query. The results limit is applied after filtering."""

    def __init__(self, source, query):
        self.source = source
        self.query = query

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
        return CachedFilterDirItems(paths, self.source.search_cache, library=self.source.library)

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        return [
            SearchResult(self.source, rank, item)
            for rank, item in enumerate(self.directory.items)
        ]
