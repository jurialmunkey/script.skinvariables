# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from collections import Counter
from jurialmunkey.ftools import cached_property
from resources.lib.multisearch.constants import PROPERTY_PREFIX
from resources.lib.shortcuts.futils import read_meta_from_file


CONTAINERS_FILE = 'special://skin/shortcuts/skinvariables-multisearch-containers.json'
FALLBACK_ID = 50
CONTAINER_PROPERTY = f'{PROPERTY_PREFIX}.Container'


class ResultsContainers:
    """Results containers of the skin by widget style, e.g. {"landscape": 50, "poster": 51, "square": 52}.

    The results are added to the container for their most common widget style, or to the fallback container when the
    style has no container. Skins without the file only use the fallback container.
    """

    def __init__(self, filepath=None):
        self.filepath = filepath or CONTAINERS_FILE

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
        return ContainerChoice(self, results)


class ContainerChoice:
    """Container for a list of search results. Ties go to the style of the first result in the list."""

    def __init__(self, containers, results):
        self.containers = containers
        self.results = results

    @cached_property
    def most_common_style(self):
        """Most common widget style of the results. Empty when there are no results."""
        return self.get_most_common_style()

    def get_most_common_style(self):
        counts = Counter(result.source.widget_style for result in self.results)
        return next((style for style, count in counts.most_common(1)), '')

    @cached_property
    def control_id(self):
        return self.get_control_id()

    def get_control_id(self):
        return self.containers.styles.get(self.most_common_style, FALLBACK_ID)
