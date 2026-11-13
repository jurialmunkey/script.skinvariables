# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.multisearch.buttons import SourceButtons
from resources.lib.multisearch.history import StoredQuery
from resources.lib.multisearch.search import MultiSearch, RESULTS_LIMIT
from resources.lib.multisearch.sources import SearchSources
from resources.lib.multisearch.template import MultiSearchWindowFile
from resources.lib.multisearch.window import MultiSearchWindow
from resources.lib.scriptwindow.controller import ScriptWindowController


# Default for the query param. An empty query param is None so it opens the window blank instead.
USE_STORED_QUERY = object()


class MultiSearchController(ScriptWindowController):
    """Writes the multi search window from the skin's window file and shows it."""

    window_file_class = MultiSearchWindowFile
    window_class = MultiSearchWindow

    def __init__(self, menu=None, skin=None, paths_file=None, limit=None, query=USE_STORED_QUERY):
        self.menu = menu
        self.skin = skin
        self.paths_file = paths_file
        self.limit = limit
        self.query = query

    @cached_property
    def sources(self):
        return SearchSources(self.menu, self.skin, self.paths_file)

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
        return SourceButtons(self.sources)

    def get_window_file(self, folder):
        return MultiSearchWindowFile(folder, self.buttons)

    def get_window_kwargs(self):
        return {
            'search': self.search,
            'buttons': self.buttons,
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
    limit=None,
    query=USE_STORED_QUERY,
    **kwargs,
):
    MultiSearchController(menu, skin, paths, limit, query).run()
