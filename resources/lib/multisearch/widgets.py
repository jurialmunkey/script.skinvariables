# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.multisearch.constants import PROPERTY_PREFIX
from resources.lib.multisearch.containers import CONTAINER_PROPERTY, FALLBACK_ID


MEDIATYPE_LIST_ID_START = 501
COUNT_PROPERTY = f'{PROPERTY_PREFIX}.Count'
TMDBHELPER_CONTAINER_PROPERTY = 'TMDbHelper.WidgetContainer'


class ResultsList:
    """Results container of the window filled with the results of a source filter button."""

    button = None

    def __init__(self, containers):
        self.containers = containers
        self.results = []
        self.control_id = FALLBACK_ID

    @property
    def properties(self):
        """Window properties for the results the list shows."""
        return self.get_properties()

    def get_properties(self):
        raise NotImplementedError

    def get_control_id(self):
        """Container for the results the list shows."""
        raise NotImplementedError

    def get_results(self, view):
        return self.button.get_results(view)

    def set_results(self, view):
        self.results = self.get_results(view)
        self.control_id = self.get_control_id()

    def clear(self):
        """Empty the list while keeping its container."""
        self.results = []


class SelectedButtonList(ResultsList):
    """Results of the selected source button, in the container for their widget style.

    The window sets the button each time another source button is selected. The list is empty while the button is
    hidden, which only happens to the always selected all sources button of the content type lists while a content type
    list shows the same results.
    """

    def __init__(self, containers, sources):
        super().__init__(containers)
        self.sources = sources

    def get_results(self, view):
        if not self.button.is_shown(self.sources, view):
            return []
        return super().get_results(view)

    def get_properties(self):
        return {
            CONTAINER_PROPERTY: str(self.control_id),
            COUNT_PROPERTY: str(len(self.results)),
        }

    def get_control_id(self):
        return self.button.get_container_choice(self.containers, self.results).control_id


class MediaTypeResultsList(ResultsList):
    """Results of one content type in its own container. The skin defines the style of the container."""

    def __init__(self, containers, button, control_id):
        super().__init__(containers)
        self.button = button
        self.control_id = control_id

    def get_properties(self):
        return {self.button.shown_property: 'true' if self.results else ''}

    def get_control_id(self):
        return self.control_id


class ResultsLists:
    """Results lists of the window. The selected list shows the results of the selected source button."""

    def __init__(self, containers, buttons):
        self.containers = containers
        self.buttons = buttons

    @cached_property
    def selected_list(self):
        return SelectedButtonList(self.containers, self.buttons.sources)

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        return [self.selected_list]

    @cached_property
    def control_ids(self):
        """Containers the lists can fill."""
        return self.get_control_ids()

    def get_control_ids(self):
        return self.containers.control_ids

    def get(self, control_id):
        """List shown in the container. KeyError when no list currently fills the container."""
        return {results_list.control_id: results_list for results_list in self.items}[control_id]

    @property
    def top_list(self):
        """Visible list with the lowest container id. The selected list when no list has results."""
        return self.get_top_list()

    def get_top_list(self):
        return min(
            (
                results_list
                for results_list in self.items
                if results_list.results
            ),
            key=lambda results_list: results_list.control_id,
            default=self.selected_list,
        )

    @property
    def hidden_lists(self):
        """Lists hidden while the results update. Every list except the top list."""
        return self.get_hidden_lists()

    def get_hidden_lists(self):
        top_list = self.top_list
        return [
            results_list
            for results_list in self.items
            if results_list is not top_list
        ]


class MediaTypeResultsLists(ResultsLists):
    """Results lists with a list for each content type after the list of all results.

    The content type lists fill the containers from 501 onwards in the order of the content type buttons.
    """

    @cached_property
    def mediatype_lists(self):
        return self.get_mediatype_lists()

    def get_mediatype_lists(self):
        return [
            MediaTypeResultsList(self.containers, button, control_id)
            for control_id, button in enumerate(self.buttons.mediatype_buttons, MEDIATYPE_LIST_ID_START)
        ]

    def get_items(self):
        return [self.selected_list, *self.mediatype_lists]

    def get_control_ids(self):
        return (
            *self.containers.control_ids,
            *(results_list.control_id for results_list in self.mediatype_lists),
        )


class WidgetContainer:
    """Window properties for the container of the top list of the window. The skin sets none by default."""

    def __init__(self, lists):
        self.lists = lists

    @property
    def properties(self):
        return self.get_properties()

    def get_properties(self):
        return {}


class TMDbHelperWidgetContainer(WidgetContainer):
    """Sets the local TMDbHelper widget container to the container of the top list of the window."""

    def get_properties(self):
        return {TMDBHELPER_CONTAINER_PROPERTY: str(self.lists.top_list.control_id)}
