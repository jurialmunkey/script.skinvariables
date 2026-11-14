# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from collections import Counter
from datetime import date
from resources.lib.kodiutils import get_localized
from resources.lib.multisearch.constants import PROPERTY_PREFIX


GENRE_SEPARATOR = ' / '
OTHER_MEDIATYPE = 'other'
MEDIATYPE_LOCALIZED_IDS = {
    'movie': 20338,
    'set': 20434,
    'tvshow': 36903,
    'season': 20373,
    'episode': 20359,
    'musicvideo': 20391,
    'artist': 557,
    'album': 558,
    'song': 179,
    OTHER_MEDIATYPE: 32103,
}
AIRED_MEDIATYPES = (
    'movie',
    'tvshow',
    'season',
    'episode',
)
PREMIERED_LENGTH = len('YYYY-MM-DD')


class ResultFilter:
    """Filter on one value of the results. An empty value lets every result through."""

    name = ''
    localized_id = 0
    reverse = False
    default_value = ''

    def __init__(self):
        self.value = self.default_value

    @property
    def property_affix(self):
        return self.name.capitalize()

    @property
    def property_name(self):
        return f'{PROPERTY_PREFIX}.{self.property_affix}'

    @property
    def properties(self):
        return {self.property_name: self.value}

    def get_values(self, result):
        """Values of the result that the filter can match. Empty when the result has none."""
        raise NotImplementedError

    def matches(self, result):
        return not self.value or self.value in self.get_values(result)

    def get_option_counts(self, results, values=()):
        """Values found in the results with how many results have each, in select dialog order.

        The chosen value and the given values are included so they stay selectable, counted as zero when no result
        has them.
        """
        counts = Counter(value for result in results for value in set(self.get_values(result)))
        counts.update(dict.fromkeys(values, 0))
        counts.update({self.value: 0} if self.value else {})
        return [(value, counts[value]) for value in sorted(counts, key=self.get_option_key, reverse=self.reverse)]

    def get_option_key(self, value):
        return value.lower()

    def get_option_label(self, value):
        """Label of the value in the select dialog."""
        return value

    def set_value(self, value):
        self.value = value

    def reset(self):
        self.set_value(self.default_value)


class ToggleFilter(ResultFilter):
    """Filter switched on and off by a button instead of chosen from a select dialog. Switched on by default."""

    default_value = 'true'

    def toggle(self):
        self.set_value('' if self.value else 'true')


class UnairedFilter(ToggleFilter):
    """Hides movies, tvshows, seasons and episodes that have not aired by today. Other results are always shown.

    Results are aired when their premiered date is today or earlier. Results without a premiered date are unaired.
    """

    name = 'unaired'
    property_affix = 'HideUnaired'

    @property
    def today(self):
        return date.today().isoformat()

    def get_premiered(self, result):
        return (result.item.infolabels.get('premiered') or '')[:PREMIERED_LENGTH]

    def get_is_aired(self, result):
        premiered = self.get_premiered(result)
        return bool(premiered) and premiered <= self.today

    def get_is_dated(self, result):
        """Whether the content type of the result has a premiered date that decides if it has aired."""
        return result.item.infolabels.get('mediatype') in AIRED_MEDIATYPES

    def matches(self, result):
        return not self.value or not self.get_is_dated(result) or self.get_is_aired(result)


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


class MediaTypeFilter(ResultFilter):
    """Matches results with the content type, such as movie or tvshow, found in their ListItem.DBType.

    Results with a type that is not a known type, or without a type, are in the other type, which is listed last.
    """

    name = 'mediatype'
    property_affix = 'DBType'
    localized_id = 467

    def get_values(self, result):
        mediatype = result.item.infolabels.get('mediatype')
        return [mediatype if mediatype in MEDIATYPE_LOCALIZED_IDS else OTHER_MEDIATYPE]

    def get_option_key(self, value):
        return (value == OTHER_MEDIATYPE, self.get_option_label(value).lower())

    def get_option_label(self, value):
        return get_localized(MEDIATYPE_LOCALIZED_IDS[value])


class ResultFilters:
    """Content type, genre, decade and unaired filters chosen in the window.

    A result is shown when it matches every filter.
    """

    def __init__(self):
        self.items = {
            result_filter.name: result_filter
            for result_filter in (
                MediaTypeFilter(),
                GenreFilter(),
                DecadeFilter(),
                UnairedFilter(),
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

    def reset(self):
        """Return every filter to its default. Unaired results are hidden again."""
        for result_filter in self.items.values():
            result_filter.reset()

    @property
    def values(self):
        """Chosen value of each filter by name. Empty for filters that let every result through."""
        return {name: result_filter.value for name, result_filter in self.items.items()}

    @property
    def properties(self):
        return {
            name: value
            for result_filter in self.items.values()
            for name, value in result_filter.properties.items()
        }
