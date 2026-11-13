# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from itertools import chain
from jurialmunkey.ftools import cached_property


class ResultsView:
    """Results of a search as the window shows them.

    The filters are applied to each source's results first. The all sources results then combine the filtered
    results with the sort method, and the limit is applied last, so filtering never shrinks the results below the
    limit when more matching results exist.
    """

    def __init__(self, request, filters, sort_method, limit):
        self.request = request
        self.filters = filters
        self.sort_method = sort_method
        self.limit = limit

    @cached_property
    def filtered_results(self):
        """Filtered results by source."""
        return self.get_filtered_results()

    def get_filtered_results(self):
        return {
            source: [result for result in results if self.filters.matches(result)]
            for source, results in self.request.results_by_source.items()
        }

    def get_sorted_items(self, source_results):
        return self.sort_method(source_results).items[:self.limit]

    @cached_property
    def all_items(self):
        return self.get_all_items()

    def get_all_items(self):
        return self.get_sorted_items(list(self.filtered_results.values()))

    def get_source_items(self, source):
        """Results of one source. Empty for a source that was not enabled for the search."""
        return self.get_sorted_items([self.filtered_results.get(source, [])])

    def has_results(self, source):
        return bool(self.filtered_results.get(source))

    @cached_property
    def all_results(self):
        """Unfiltered results of every source."""
        return self.get_all_results()

    def get_all_results(self):
        return list(chain.from_iterable(self.request.results_by_source.values()))

    def get_source_results(self, source):
        """Unfiltered results of one source."""
        return self.request.results_by_source.get(source, [])

    def get_filter_options(self, result_filter, scope_results):
        return FilterOptions(self, result_filter, scope_results)


class FilterOptions:
    """Values to choose for a filter from the results in scope that match the other filters.

    Each count is the number of results the list shows when the value is chosen, so it is capped at the limit.
    """

    def __init__(self, view, result_filter, scope_results):
        self.view = view
        self.result_filter = result_filter
        self.scope_results = scope_results

    @cached_property
    def matching_results(self):
        """Results in scope that match every filter apart from this one."""
        return self.get_matching_results()

    def get_matching_results(self):
        return [
            result
            for result in self.scope_results
            if self.view.filters.matches(result, excluded=self.result_filter)
        ]

    def get_count(self, count):
        return min(count, self.view.limit)

    @cached_property
    def any_count(self):
        """Results shown when the filter is cleared."""
        return self.get_count(len(self.matching_results))

    @cached_property
    def items(self):
        """Values with the number of results shown when each is chosen."""
        return self.get_items()

    def get_items(self):
        return [
            (value, self.get_count(count))
            for value, count in self.result_filter.get_option_counts(self.matching_results)
        ]

    @cached_property
    def values(self):
        return [value for value, count in self.items]
