# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.multisearch.constants import PROPERTY_PREFIX


GENRE_SEPARATOR = ' / '


class ResultFilter:
    """Filter on one value of the results. An empty value lets every result through."""

    name = ''
    localized_id = 0
    reverse = False

    def __init__(self):
        self.value = ''

    @property
    def property_name(self):
        return f'{PROPERTY_PREFIX}.{self.name.capitalize()}'

    @property
    def properties(self):
        return {self.property_name: self.value}

    def get_values(self, result):
        """Values of the result that the filter can match. Empty when the result has none."""
        raise NotImplementedError

    def matches(self, result):
        return not self.value or self.value in self.get_values(result)

    def get_options(self, results):
        """Values found in the results, including the chosen value so it stays selectable."""
        values = {value for result in results for value in self.get_values(result)}
        values.update([self.value] if self.value else [])
        return sorted(values, key=self.get_option_key, reverse=self.reverse)

    def get_option_key(self, value):
        return value.lower()

    def set_value(self, value):
        self.value = value


class GenreFilter(ResultFilter):
    """Matches results with the genre. Results with several genres count for each of them."""

    name = 'genre'
    localized_id = 515

    def get_values(self, result):
        genres = result.item.infolabels.get('genre') or []
        genres = genres.split(GENRE_SEPARATOR) if isinstance(genres, str) else genres
        return [genre.strip() for genre in genres if genre.strip()]


class DecadeFilter(ResultFilter):
    """Matches results with a year in the decade, such as 1980 to 1989 for 1980s. Newest decades are listed first."""

    name = 'decade'
    localized_id = 32099
    reverse = True

    def get_values(self, result):
        try:
            year = int(result.item.infolabels.get('year'))
        except (TypeError, ValueError):  # Results without a year are in no decade.
            return []
        return [f'{year // 10 * 10}s']


class ResultFilters:
    """Genre and decade filters chosen in the window. A result is shown when it matches every filter."""

    def __init__(self):
        self.items = {
            result_filter.name: result_filter
            for result_filter in (
                GenreFilter(),
                DecadeFilter(),
            )
        }

    def get(self, name):
        return self.items[name]

    def matches(self, result, excluded=None):
        """Whether the result matches every filter apart from the excluded one."""
        return all(
            result_filter.matches(result)
            for result_filter in self.items.values()
            if result_filter is not excluded
        )

    @property
    def properties(self):
        return {
            name: value
            for result_filter in self.items.values()
            for name, value in result_filter.properties.items()
        }
