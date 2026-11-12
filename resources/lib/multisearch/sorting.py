# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from itertools import chain, zip_longest
from jurialmunkey.ftools import cached_property
from resources.lib.kodiutils import get_localized


class ResultsSort:
    """Combines the results of each source into one list sorted by an infolabel."""

    key = ''
    reverse = False
    localized_id = 0

    def __init__(self, source_results):
        self.source_results = source_results

    @classmethod
    def get_label(cls):
        return get_localized(cls.localized_id)

    def get_sort_value(self, result):
        return result.get_sort_value(self.key)

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        return sorted(chain.from_iterable(self.source_results), key=self.get_sort_value, reverse=self.reverse)


class RankSort(ResultsSort):
    """Interleaves the sources by rank: the first result of each source, then the second result of each source."""

    localized_id = 35344

    def get_items(self):
        return [
            result
            for rank_results in zip_longest(*self.source_results)
            for result in rank_results
            if result is not None
        ]


class TitleSort(ResultsSort):
    key = 'title'
    localized_id = 556


class YearSort(ResultsSort):
    key = 'year'
    reverse = True
    localized_id = 562


class PremieredSort(ResultsSort):
    key = 'premiered'
    reverse = True
    localized_id = 20473


class RatingSort(ResultsSort):
    key = 'rating'
    reverse = True
    localized_id = 563


SORT_METHODS = (
    RankSort,
    TitleSort,
    YearSort,
    PremieredSort,
    RatingSort,
)
