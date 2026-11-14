# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from itertools import chain
from jurialmunkey.ftools import cached_property
from resources.lib.kodiutils import get_localized
from resources.lib.multisearch.results import UniqueResults


def get_count_label(label, count):
    return f'{label} ({count})'


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
    def unique_items(self):
        """Filtered results of every source, sorted and without duplicates, before the limit."""
        return self.get_unique_items()

    def get_unique_items(self):
        """Duplicates are removed after sorting, keeping the copy sorted first."""
        sorted_items = self.sort_method(list(self.filtered_results.values())).items
        return UniqueResults(sorted_items).items

    @cached_property
    def all_items(self):
        return self.get_all_items()

    def get_all_items(self):
        return self.unique_items[:self.limit]

    def get_mediatype_unique_items(self, result_filter):
        """Filtered results of every source with the content type of the filter, before the limit."""
        return [result for result in self.unique_items if result_filter.matches(result)]

    def get_mediatype_items(self, result_filter):
        """Results of every source with the content type of the filter. The limit is applied after filtering."""
        return self.get_mediatype_unique_items(result_filter)[:self.limit]

    def get_source_items(self, source):
        """Results of one source. Empty for a source that was not enabled for the search."""
        return self.get_sorted_items([self.filtered_results.get(source, [])])

    def has_results(self, source):
        return bool(self.filtered_results.get(source))

    @cached_property
    def sources_with_results(self):
        """Sources with filtered results."""
        return self.get_sources_with_results()

    def get_sources_with_results(self):
        return [source for source, results in self.filtered_results.items() if results]

    def has_only_source(self, source):
        """Whether the source is the only one with filtered results, so it shows the same results as all."""
        return self.sources_with_results == [source]

    def get_mediatype_count(self, result_filter):
        return len(self.get_mediatype_unique_items(result_filter))

    def has_mediatype(self, result_filter):
        """Whether any of the results of every source have the content type of the filter."""
        return self.get_mediatype_count(result_filter) > 0

    def has_only_mediatype(self, result_filter):
        """Whether every one of the results of every source has the content type of the filter."""
        return self.has_mediatype(result_filter) and self.get_mediatype_count(result_filter) == len(self.unique_items)

    @cached_property
    def all_results(self):
        """Unfiltered results of every source without duplicates."""
        return self.get_all_results()

    def get_all_results(self):
        return UniqueResults(chain.from_iterable(self.request.results_by_source.values())).items

    def get_filter_options(self, result_filter):
        return FilterOptions(self, result_filter)


class FilterOptions:
    """Values to choose for a filter from the results of every source that match the other filters.

    The options do not depend on the selected source button, which only chooses which of the results are shown.
    Each count is the number of results the all sources list shows when the value is chosen, so it is capped at the
    limit.
    """

    def __init__(self, view, result_filter):
        self.view = view
        self.result_filter = result_filter

    @cached_property
    def matching_results(self):
        """Results of every source that match every filter apart from this one."""
        return self.get_matching_results()

    def get_matching_results(self):
        return [
            result
            for result in self.view.all_results
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

    def get_option_counts(self):
        return self.result_filter.get_option_counts(self.matching_results)

    def get_items(self):
        return [
            (value, self.get_count(count))
            for value, count in self.get_option_counts()
        ]

    @cached_property
    def values(self):
        return [value for value, count in self.items]

    def get_label(self, label, count):
        return get_count_label(label, count)

    @cached_property
    def labels(self):
        """Select dialog labels: Any followed by the values."""
        return self.get_labels()

    def get_labels(self):
        return [
            self.get_label(get_localized(32100), self.any_count),
            *(self.get_label(self.result_filter.get_option_label(value), count) for value, count in self.items),
        ]


class DiscoverResultsView(ResultsView):
    """Results of a search with a discover source enabled. The filters offer every value TMDb can discover."""

    def __init__(self, request, filters, sort_method, limit, catalogue):
        super().__init__(request, filters, sort_method, limit)
        self.catalogue = catalogue

    def get_filter_options(self, result_filter):
        return DiscoverFilterOptions(self, result_filter)


class DiscoverFilterOptions(FilterOptions):
    """Values to choose for a filter, including every value TMDb can discover for it.

    Counts are hidden because choosing a value looks up new discover results.
    """

    def get_option_counts(self):
        values = self.view.catalogue.get_values(self.result_filter)
        return self.result_filter.get_option_counts(self.matching_results, values)

    def get_label(self, label, count):
        return label
