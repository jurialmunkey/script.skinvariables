# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.multisearch.query import SearchQuery
from resources.lib.multisearch.sorting import SORT_METHODS
from resources.lib.multisearch.workers import SearchDispatcher, SearchRequest


RESULTS_LIMIT = 100


class MultiSearch:
    """Search settings of the window and the searches sent to the worker.

    Only the most recently submitted search is current so results from searches that finish later are discarded.
    """

    def __init__(self, sources, limit=RESULTS_LIMIT):
        self.sources = sources
        self.limit = limit
        self.sort_position = 0
        self.current = None
        self.dispatcher = SearchDispatcher()

    @property
    def sort_method(self):
        return SORT_METHODS[self.sort_position]

    @property
    def sort_labels(self):
        return [sort_method.get_label() for sort_method in SORT_METHODS]

    def set_sort_position(self, position):
        self.sort_position = position

    def get_request(self, text, callback):
        return SearchRequest(SearchQuery(text), self.sources.enabled, self.sort_method, self.limit, callback)

    def submit(self, text, callback):
        self.current = self.get_request(text, callback)
        self.dispatcher.submit(self.current)

    def is_current(self, request):
        return request is self.current

    def clear(self):
        self.current = None
        self.dispatcher.clear()

    def close(self):
        self.clear()
        self.dispatcher.join()
