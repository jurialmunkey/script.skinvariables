# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from urllib.parse import parse_qs, quote, urlencode, urlsplit
from jurialmunkey.ftools import cached_property, threaded_cached_property
from resources.lib.filterdir.paths import FilterDirPaths
from resources.lib.kodiutils import get_localized
from resources.lib.multisearch.results import CachedFilterDirItems, SourceResults
from resources.lib.multisearch.sorting import PremieredSort, RankSort, RatingSort, TitleSort, YearSort
from resources.lib.multisearch.sources import SearchSource, SearchSources, get_path_origin


TMDBHELPER_PLUGIN = 'plugin://plugin.video.themoviedb.helper/'
TMDBHELPER_ICON = 'special://home/addons/plugin.video.themoviedb.helper/icon.png'
DISCOVER_TARGET = 'videos'
DISCOVER_LIBRARY = 'video'
DISCOVER_DECADES = tuple(f'{year}s' for year in range(2020, 1890, -10))


class DiscoverParams:
    """TMDbHelper discover path for the search text with the genre, decade and sort method of the search.

    The search text is passed as with_text_query, which TMDb accepts although it is undocumented. TMDbHelper adds the
    params to the TMDb URL without encoding them again, so the search text is encoded twice.
    """

    def __init__(self, source, query, options):
        self.source = source
        self.query = query
        self.options = options

    @cached_property
    def query_params(self):
        """Without search text the results are discovered from the genre, decade and sort method alone."""
        return self.get_query_params()

    def get_query_params(self):
        return {'with_text_query': self.query.encoded} if self.query.raw else {}

    @cached_property
    def genre_params(self):
        return self.get_genre_params()

    def get_genre_params(self):
        """TMDb id of the genre for the source's type. TMDbHelper only converts names of genres shared by both types."""
        genre = self.options.values['genre']
        return {'with_genres': self.source.genres.ids[genre], 'with_id': 'True'} if genre else {}

    @cached_property
    def decade_params(self):
        return self.get_decade_params()

    def get_decade_params(self):
        decade = self.options.values['decade']
        if not decade:
            return {}
        start = int(decade[:-1])
        return {
            f'{self.source.date_key}.gte': f'{start}-01-01',
            f'{self.source.date_key}.lte': f'{start + 9}-12-31',
        }

    @cached_property
    def sort_params(self):
        return {'sort_by': self.source.sort_values[self.options.sort_method]}

    @cached_property
    def params(self):
        return self.get_params()

    def get_params(self):
        return {
            'info': 'discover',
            'tmdb_type': self.source.tmdb_type,
            'nextpage': 'false',
            **self.query_params,
            **self.genre_params,
            **self.decade_params,
            **self.sort_params,
        }

    @cached_property
    def path(self):
        return f'{TMDBHELPER_PLUGIN}?{urlencode(self.params, quote_via=quote)}'


class DiscoverResults(SourceResults):
    """All items of one discover source for one search. The search options are part of the discover path."""

    def __init__(self, source, query, options):
        super().__init__(source, query)
        self.options = options

    def get_path(self):
        return DiscoverParams(self.source, self.query, self.options).path


class DiscoverGenres:
    """TMDb genre ids by name for one TMDb type in the TMDbHelper language. The lookup is kept for a day.

    Each item of the TMDbHelper genres list links to its discover path, which has the genre id in with_genres.
    """

    def __init__(self, search_cache, tmdb_type):
        self.search_cache = search_cache
        self.tmdb_type = tmdb_type

    @cached_property
    def paths(self):
        return FilterDirPaths((f'{TMDBHELPER_PLUGIN}?info=genres&tmdb_type={self.tmdb_type}',))

    @cached_property
    def directory(self):
        return CachedFilterDirItems(self.paths, self.search_cache, library=DISCOVER_LIBRARY)

    @staticmethod
    def get_id(item):
        return parse_qs(urlsplit(item.path).query)['with_genres'][0]

    @threaded_cached_property
    def ids(self):
        """Read by the search workers and by the window, so the genres list is only looked up once."""
        return self.get_ids()

    def get_ids(self):
        return {item.infolabels['title']: self.get_id(item) for item in self.directory.items}


class DiscoverSource(SearchSource):
    """TMDbHelper discover source. The genre, decade and sort method of the search are looked up by TMDb.

    Searches without search text too, discovering results from the genre, decade and sort method alone. Skipped for
    genres that TMDb only has for the other type.
    """

    discover = True
    tmdb_type = ''
    localized_id = 0
    date_key = ''
    sort_values = {}

    def __init__(self, index, search_cache, widget_style=None):
        super().__init__(index, self.get_meta(widget_style), {}, search_cache)

    def get_meta(self, widget_style):
        return {
            'label': get_localized(self.localized_id),
            'icon': TMDBHELPER_ICON,
            'target': DISCOVER_TARGET,
            'widget_style': widget_style or '',
        }

    def get_template(self):
        return ''

    def get_origin(self):
        return get_path_origin(TMDBHELPER_PLUGIN)

    @cached_property
    def genres(self):
        return DiscoverGenres(self.search_cache, self.tmdb_type)

    def accepts(self, query, options):
        genre = options.values['genre']
        return not genre or genre in self.genres.ids

    def get_cache_key(self, query, options):
        return (query.raw, options.key)

    def get_source_results(self, query, options):
        return DiscoverResults(self, query, options)


class MovieDiscoverSource(DiscoverSource):
    tmdb_type = 'movie'
    localized_id = 32101
    date_key = 'primary_release_date'
    sort_values = {
        RankSort: 'popularity.desc',
        TitleSort: 'title.asc',
        YearSort: 'primary_release_date.desc',
        PremieredSort: 'primary_release_date.desc',
        RatingSort: 'vote_average.desc',
    }


class TvDiscoverSource(DiscoverSource):
    tmdb_type = 'tv'
    localized_id = 32102
    date_key = 'first_air_date'
    sort_values = {
        RankSort: 'popularity.desc',
        TitleSort: 'name.asc',
        YearSort: 'first_air_date.desc',
        PremieredSort: 'first_air_date.desc',
        RatingSort: 'vote_average.desc',
    }


DISCOVER_SOURCE_CLASSES = (
    MovieDiscoverSource,
    TvDiscoverSource,
)


class DiscoverSearchSources(SearchSources):
    """TMDbHelper discover sources for movies and tvshows followed by the search widgets of the shortcuts menu."""

    def __init__(self, menu=None, skin=None, paths_file=None, widget_style=None):
        super().__init__(menu, skin, paths_file)
        self.widget_style = widget_style

    @cached_property
    def discover_items(self):
        return self.get_discover_items()

    def get_discover_items(self):
        """Indexed after the shortcuts menu entries, matching how the shortcut sources are indexed."""
        return [
            source_class(index, self.search_cache, self.widget_style)
            for index, source_class in enumerate(DISCOVER_SOURCE_CLASSES, len(self.menu_meta))
        ]

    def get_items(self):
        """Discover sources are always listed first."""
        return [*self.discover_items, *super().get_items()]


class DiscoverCatalogue:
    """Every value the enabled discover sources can look up for each filter.

    Filters that are not passed to TMDb, such as the content type, have no catalogue values.
    """

    def __init__(self, sources):
        self.sources = sources

    @cached_property
    def genre_values(self):
        """Genres of each enabled discover source. Looked up when the genre dialog first opens."""
        return self.get_genre_values()

    def get_genre_values(self):
        genres = (genre for source in self.sources for genre in source.genres.ids)
        return list(dict.fromkeys(genres))

    @property
    def decade_values(self):
        return DISCOVER_DECADES

    def get_values(self, result_filter):
        try:
            return getattr(self, f'{result_filter.name}_values')
        except AttributeError:  # Filters without catalogue values only offer the values found in the results.
            return ()
