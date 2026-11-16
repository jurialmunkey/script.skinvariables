# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.multisearch.discover import DiscoverCatalogue
from resources.lib.multisearch.filters import ResultFilters
from resources.lib.multisearch.options import SearchOptions
from resources.lib.multisearch.progress import NO_PROGRESS
from resources.lib.multisearch.query import SearchQuery
from resources.lib.multisearch.sorting import SORT_METHODS
from resources.lib.multisearch.view import DiscoverResultsView, ResultsView
from resources.lib.multisearch.workers import SearchDispatcher, SearchRequest


RESULTS_LIMIT = 100


class MultiSearch:
    """Search settings of the window and the searches sent to the workers.

    Only the most recently submitted search is current so results from searches that finish later are discarded.
    """

    def __init__(self, sources, limit=RESULTS_LIMIT, progress=NO_PROGRESS):
        self.sources = sources
        self.limit = limit
        self.sort_position = 0
        self.filters = ResultFilters()
        self.current = None
        self.dispatcher = SearchDispatcher(sources, progress)

    @property
    def sort_method(self):
        return SORT_METHODS[self.sort_position]

    @property
    def sort_labels(self):
        return [sort_method.get_label() for sort_method in SORT_METHODS]

    def set_sort_position(self, position):
        self.sort_position = position

    def reset(self):
        """Return the filters and sources to their defaults. The sort method is kept."""
        self.filters.reset()
        self.sources.reset()

    def get_options(self):
        return SearchOptions(self.filters, self.sort_method)

    def get_sources(self, query, options):
        """Enabled sources that search for the query and options.

        Only discover sources search without search text. Discover sources skip genres TMDb only has for the other type.
        """
        return [source for source in self.sources.enabled if source.accepts(query, options)]

    def can_search(self, text):
        """Whether an enabled source searches for the text. Otherwise the results are emptied."""
        return bool(self.get_sources(SearchQuery(text), self.get_options()))

    def get_request(self, text, callback):
        query = SearchQuery(text)
        options = self.get_options()
        return SearchRequest(query, options, self.get_sources(query, options), callback)

    def get_view(self, request):
        """Results of the search with the current filters, sort method and limit.

        While a discover source is enabled, the filters offer every value the discover sources can look up.
        """
        discover_sources = self.sources.discover_enabled
        if discover_sources:
            catalogue = DiscoverCatalogue(discover_sources)
            return DiscoverResultsView(request, self.filters, self.sort_method, self.limit, catalogue)
        return ResultsView(request, self.filters, self.sort_method, self.limit)

    def submit(self, text, callback):
        self.current = self.get_request(text, callback)
        self.dispatcher.submit(self.current)

    def delay_settle(self):
        """Wait the settle delay again before the waiting searches start."""
        self.dispatcher.delay_settle()

    def is_current(self, request):
        return request is self.current

    def clear(self):
        self.current = None
        self.dispatcher.clear()

    def close(self):
        self.clear()
        self.dispatcher.stop()
        self.sources.search_cache.stop()
