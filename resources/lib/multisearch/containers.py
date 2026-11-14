# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from collections import Counter
from jurialmunkey.ftools import cached_property
from resources.lib.multisearch.constants import PROPERTY_PREFIX
from resources.lib.multisearch.filters import MediaTypeFilter
from resources.lib.shortcuts.futils import read_meta_from_file


CONTAINERS_FILE = 'special://skin/shortcuts/skinvariables-multisearch-containers.json'
STYLES_FILE = 'special://skin/shortcuts/skinvariables-multisearch-styles.json'
FALLBACK_ID = 50
CONTAINER_PROPERTY = f'{PROPERTY_PREFIX}.Container'


class MediaTypeStyles:
    """Widget style of the skin by content type, e.g. {"movie": "poster", "tvshow": "poster", "episode": "landscape"}.

    Results with a content type that has no style use the widget style of their source. Results that are not one of
    the known content types use the style of the other type. Skins without the file style every result by its source.
    """

    def __init__(self, filepath=None):
        self.filepath = filepath or STYLES_FILE

    @cached_property
    def mediatype_filter(self):
        """Content type of the results, the same as the content type filter and buttons."""
        return MediaTypeFilter()

    @cached_property
    def items(self):
        """Widget style by content type."""
        return self.get_items()

    def get_items(self):
        return read_meta_from_file(self.filepath) or {}

    def get(self, mediatype):
        return self.items[mediatype]

    def get_style(self, result):
        mediatype, = self.mediatype_filter.get_values(result)
        return self.items.get(mediatype, result.source.widget_style)


class ResultsContainers:
    """Results containers of the skin by widget style, e.g. {"landscape": 50, "poster": 51, "square": 52}.

    The results are added to the container for their most common widget style, or to the fallback container when the
    style has no container. Skins without the file only use the fallback container.

    When the skin defines widget styles by content type, the results count towards the style of their content type
    instead of the style of their source, and the results of a content type always use the style of that type.
    """

    def __init__(self, filepath=None, mediatype_styles=None):
        self.filepath = filepath or CONTAINERS_FILE
        self.mediatype_styles = mediatype_styles or MediaTypeStyles()

    @cached_property
    def styles(self):
        """Container id by widget style."""
        return self.get_styles()

    def get_styles(self):
        return {
            style: int(control_id)
            for style, control_id in (read_meta_from_file(self.filepath) or {}).items()
        }

    @cached_property
    def control_ids(self):
        """Fallback container followed by the containers of the styles."""
        return tuple(dict.fromkeys((FALLBACK_ID, *self.styles.values())))

    @cached_property
    def toggled_ids(self):
        """Containers shown only while the results use them. None when the fallback container is the only one."""
        return self.control_ids if self.styles else ()

    @staticmethod
    def get_visible_condition(control_id):
        return f'String.IsEqual(Window.Property({CONTAINER_PROPERTY}),{control_id})'

    def get_choice(self, results):
        """Container for the most common style of the results."""
        if self.mediatype_styles.items:
            return MediaTypeContainerChoice(self, results)
        return ContainerChoice(self, results)

    def get_mediatype_choice(self, mediatype, results):
        """Container for the results of one content type. Types without a style use the most common style."""
        try:
            return FixedContainerChoice(self, results, self.mediatype_styles.get(mediatype))
        except KeyError:
            return self.get_choice(results)


class ContainerChoice:
    """Container for a list of search results. Ties go to the style of the first result in the list."""

    def __init__(self, containers, results):
        self.containers = containers
        self.results = results

    def get_result_style(self, result):
        """Widget style the result counts towards."""
        return result.source.widget_style

    @cached_property
    def most_common_style(self):
        """Most common widget style of the results. Empty when there are no results."""
        return self.get_most_common_style()

    def get_most_common_style(self):
        counts = Counter(self.get_result_style(result) for result in self.results)
        return next((style for style, count in counts.most_common(1)), '')

    @cached_property
    def control_id(self):
        return self.get_control_id()

    def get_control_id(self):
        return self.containers.styles.get(self.most_common_style, FALLBACK_ID)


class MediaTypeContainerChoice(ContainerChoice):
    """Container for a list of search results counted by the widget style of their content type.

    Content types with the same style count together towards it.
    """

    def get_result_style(self, result):
        return self.containers.mediatype_styles.get_style(result)


class FixedContainerChoice(ContainerChoice):
    """Container for a list of search results that always use one widget style."""

    def __init__(self, containers, results, style):
        super().__init__(containers, results)
        self.style = style

    def get_most_common_style(self):
        return self.style
