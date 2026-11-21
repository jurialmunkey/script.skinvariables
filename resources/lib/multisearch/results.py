# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from urllib.parse import parse_qs, parse_qsl, quote, urlencode, urlsplit
import xbmc
import xbmcaddon
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

    @cached_property
    def context_menu(self):
        if self.source.origin != 'plugin.video.themoviedb.helper':
            return ()

        addon = xbmcaddon.Addon('plugin.video.themoviedb.helper')
        item_type = self.item.infolabels.get('mediatype') or ''
        query_type = parse_qs(urlsplit(self.source.template).query).get('tmdb_type', [''])[0]
        type_map = {
            'movie': 'movie',
            'tv': 'tv',
            'tvshow': 'tv',
            'season': 'tv',
            'episode': 'tv',
            'set': 'collection',
            'collection': 'collection',
            'actor': 'person',
            'person': 'person',
            'keyword': 'keyword',
        }
        tmdb_type = type_map.get(item_type) or type_map.get(query_type) or query_type or item_type
        tmdb_id = (
            self.item.infoproperties.get('tvshow.tmdb_id')
            if item_type in ('season', 'episode')
            else None
        ) or self.item.uniqueids.get('tmdb') or self.item.infoproperties.get('tmdb_id')
        tmdb_id = str(tmdb_id or '').strip()
        if not tmdb_id.isdigit() or not tmdb_type:
            return ()

        season = str(self.item.infolabels.get('season') or '').strip()
        episode = str(self.item.infolabels.get('episode') or '').strip()
        context_menu = []
        if item_type in ('movie', 'tvshow', 'season', 'episode'):
            title = self.item.infolabels.get('title') or self.item.label
            params = f'set_chosenplayer={title},tmdb_type={tmdb_type},tmdb_id={tmdb_id}'
            if item_type in ('season', 'episode'):
                params += f',season={season}'
                if item_type == 'episode':
                    params += f',episode={episode}'
            label = addon.getLocalizedString(32476)
            if label:
                context_menu.append((
                    label,
                    f'RunScript(plugin.video.themoviedb.helper,{params})',
                ))

        options = (
            ('contextmenu_related_lists', 32235, 'related_lists', True),
            ('contextmenu_sync_options', 32549, 'sync_options', True),
            ('contextmenu_refresh_details', 32233, 'refresh_details', True),
            (
                'contextmenu_modify_artwork',
                32118,
                'modify_artwork',
                item_type in ('movie', 'tvshow', 'season', 'episode'),
            ),
            (
                'contextmenu_add_to_library',
                20444,
                'add_to_library',
                item_type in ('movie', 'tvshow', 'season', 'episode'),
            ),
        )
        for setting, label_id, method, eligible in options:
            if item_type in ('season', 'episode') and method != 'add_to_library':
                eligible = eligible and bool(season) and (item_type != 'episode' or bool(episode))
            if not eligible or addon.getSetting(setting).lower() != 'true':
                continue

            option_type = 'tv' if item_type in ('season', 'episode') else tmdb_type
            params = f'tmdb_type={option_type},tmdb_id={tmdb_id}'
            if method != 'add_to_library' and item_type in ('season', 'episode'):
                params += f',season={season}'
                if item_type == 'episode':
                    params += f',episode={episode}'
            label = (
                addon.getLocalizedString(label_id)
                if label_id != 20444
                else xbmc.getLocalizedString(label_id)
            )
            if label:
                context_menu.append((label, f'RunScript(plugin.video.themoviedb.helper,{method},{params})'))

        if addon.getSetting('contextmenu_play_random').lower() == 'true':
            play_random = self.get_play_random_context_item(addon)
            if play_random:
                context_menu.append(play_random)
        return tuple(context_menu)

    def get_play_random_context_item(self, addon):
        if not self.item.is_folder or self.item.infoproperties.get('specialseason'):
            return

        path = self.item.path
        if path.partition('?')[0].rstrip('/') != 'plugin://plugin.video.themoviedb.helper':
            return

        query_parts = path.partition('?')[2].split('&&')
        params = dict(parse_qsl(query_parts[0], keep_blank_values=True))
        route = params.get('info')
        excluded_routes = (
            'dir_settings',
            'user_discover',
            'trakt_authenticate',
            'trakt_discover',
            'fanart',
            'posters',
            'images',
            'episode_thumbs',
            'reviews',
            'videos',
        )
        search_routes = ('search', 'trakt_searchlists', 'mdblist_searchlists')
        if route in excluded_routes or route in ('play', 'details'):
            return
        if params.get('clear_cache') or params.get('method'):
            return
        if route in search_routes and not params.get('query'):
            return

        if route == 'flatseasons':
            params['info'] = 'seasons'
        for key in ('widget', 'reload', 'update_listing'):
            params.pop(key, None)
        query = '&&'.join([urlencode(sorted(params.items())), *query_parts[1:]])
        path = quote(f'plugin://plugin.video.themoviedb.helper/?{query}', safe='')
        label = addon.getLocalizedString(32767)
        if label:
            return label, f'RunScript(plugin.video.themoviedb.helper,play_random={path})'

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
    """Directory items read from the search cache when stored there, otherwise looked up and stored.

    Stale items are returned straight away and looked up again in the background for later searches.
    """

    def __init__(self, paths, search_cache, library=None):
        super().__init__(paths, library=library)
        self.search_cache = search_cache

    def get_lookup_directory(self, path):
        return super().get_directory(path)

    def get_stored_directory(self, path):
        directory = self.get_lookup_directory(path)
        self.search_cache.set(self.library, path, directory)
        return directory

    def get_cached_directory(self, path, entry):
        if entry.is_stale:
            self.search_cache.refresh(self.library, path, self.get_lookup_directory)
        return entry.directory

    def get_directory(self, path):
        entry = self.search_cache.get(self.library, path)
        if entry is None:
            return self.get_stored_directory(path)
        return self.get_cached_directory(path, entry)


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
