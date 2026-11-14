# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.multisearch.buttons import MediaTypeButtons, NoGrouplistButtons, SourceButtons
from resources.lib.multisearch.containers import MediaTypeStyles, ResultsContainers
from resources.lib.multisearch.discover import DiscoverSearchSources
from resources.lib.multisearch.history import StoredQuery
from resources.lib.multisearch.search import MultiSearch, RESULTS_LIMIT
from resources.lib.multisearch.sources import SearchSources
from resources.lib.multisearch.template import MultiSearchWindowFile
from resources.lib.multisearch.widgets import (
    MediaTypeResultsLists,
    ResultsLists,
    TMDbHelperWidgetContainer,
    WidgetContainer,
)
from resources.lib.multisearch.window import MultiSearchWindow
from resources.lib.scriptwindow.controller import ScriptWindowController


# Default for the query param. An empty query param is None so it opens the window blank instead.
USE_STORED_QUERY = object()


class MultiSearchController(ScriptWindowController):
    """Writes the multi search window from the skin's window file and shows it.

    The TMDbHelper discover sources for movies and tvshows follow the shortcut sources unless the skin passes the
    no_discover param. Their results use the widget style of the discover_style param.

    The source grouplist only has buttons for all sources and each content type when the skin passes the
    no_source_buttons param.

    The skin passes the mediatype_lists param for a window without the source grouplist. Lists 501 to 510 each show
    the results of one content type, in the order of the content type buttons, alongside the list of all results.

    The skin passes the tmdbhelper_container param to set the TMDbHelper.WidgetContainer window property to the
    container of the visible list with the lowest id. TMDbHelper reads it from the window when the skin enables
    TMDbHelper.UseLocalWidgetContainer.
    """

    window_file_class = MultiSearchWindowFile
    window_class = MultiSearchWindow

    def __init__(
        self,
        menu=None,
        skin=None,
        paths_file=None,
        containers_file=None,
        limit=None,
        query=USE_STORED_QUERY,
        no_discover=False,
        discover_style=None,
        styles_file=None,
        no_source_buttons=False,
        mediatype_lists=False,
        tmdbhelper_container=False,
    ):
        self.menu = menu
        self.skin = skin
        self.paths_file = paths_file
        self.containers_file = containers_file
        self.limit = limit
        self.query = query
        self.no_discover = no_discover
        self.discover_style = discover_style
        self.styles_file = styles_file
        self.no_source_buttons = no_source_buttons
        self.mediatype_lists = mediatype_lists
        self.tmdbhelper_container = tmdbhelper_container

    @cached_property
    def sources(self):
        return self.get_sources()

    def get_sources(self):
        if self.no_discover:
            return SearchSources(self.menu, self.skin, self.paths_file)
        return DiscoverSearchSources(self.menu, self.skin, self.paths_file, self.discover_style)

    @cached_property
    def mediatype_styles(self):
        return MediaTypeStyles(self.styles_file)

    @cached_property
    def containers(self):
        return ResultsContainers(self.containers_file, self.mediatype_styles)

    @cached_property
    def results_limit(self):
        return int(self.limit or RESULTS_LIMIT)

    @cached_property
    def search(self):
        return MultiSearch(self.sources, self.results_limit)

    @cached_property
    def stored_query(self):
        return StoredQuery(self.sources.menu)

    @cached_property
    def opening_query(self):
        """Search text the window opens with. The stored search unless the query param gives one or is empty."""
        return self.get_opening_query()

    def get_opening_query(self):
        if self.query is USE_STORED_QUERY:
            return self.stored_query.value
        return self.query or ''

    @cached_property
    def buttons(self):
        return self.get_buttons()

    def get_buttons(self):
        if self.mediatype_lists:
            return NoGrouplistButtons(self.sources)
        if self.no_source_buttons:
            return MediaTypeButtons(self.sources)
        return SourceButtons(self.sources)

    @cached_property
    def lists(self):
        return self.get_lists()

    def get_lists(self):
        if self.mediatype_lists:
            return MediaTypeResultsLists(self.containers, self.buttons)
        return ResultsLists(self.containers, self.buttons)

    @cached_property
    def widget_container(self):
        return self.get_widget_container()

    def get_widget_container(self):
        if self.tmdbhelper_container:
            return TMDbHelperWidgetContainer(self.lists)
        return WidgetContainer(self.lists)

    def get_window_file(self, folder):
        return MultiSearchWindowFile(folder, self.buttons, self.containers)

    def get_window_kwargs(self):
        return {
            'search': self.search,
            'buttons': self.buttons,
            'lists': self.lists,
            'widget_container': self.widget_container,
            'opening_query': self.opening_query,
            'stored_query': self.stored_query,
        }

    def get_result(self, window):
        # The window has closed so drop the queued search and wait for the running searches.
        window.stop()


def run_multisearch(
    run_multisearch=None,
    menu=None,
    skin=None,
    paths=None,
    containers=None,
    limit=None,
    query=USE_STORED_QUERY,
    no_discover=False,
    discover_style=None,
    styles=None,
    no_source_buttons=False,
    mediatype_lists=False,
    tmdbhelper_container=False,
    **kwargs,
):
    MultiSearchController(
        menu,
        skin,
        paths,
        containers,
        limit,
        query,
        no_discover,
        discover_style,
        styles,
        no_source_buttons,
        mediatype_lists,
        tmdbhelper_container,
    ).run()
