# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.multisearch.buttons import MediaTypeButtons, NoSourceListButtons, SourceButtons, SourceOnlyButtons
from resources.lib.multisearch.containers import MediaTypeStyles, ResultsContainers
from resources.lib.multisearch.discover import DiscoverSearchSources
from resources.lib.multisearch.history import StoredQuery
from resources.lib.multisearch.progress import NO_PROGRESS, SearchProgress
from resources.lib.multisearch.search import MultiSearch, RESULTS_LIMIT
from resources.lib.multisearch.sourcelist import NoSourceList, SourceList
from resources.lib.multisearch.sourcepicker import SingleSourcePicker, SourcesPicker
from resources.lib.multisearch.sources import SearchSources
from resources.lib.multisearch.template import MultiSearchWindowFile
from resources.lib.multisearch.widgets import (
    MediaTypeResultsLists,
    NoAllMediaTypeResultsLists,
    ResultsLists,
    TMDbHelperWidgetContainer,
    WidgetContainer,
)
from resources.lib.multisearch.window import MultiSearchWindow
from resources.lib.scriptwindow.controller import ScriptWindowController


# Default for the query param. An empty query param is None so it opens the window blank instead.
USE_STORED_QUERY = object()

# Buttons of the source list for each value of the source_buttons param.
SOURCE_BUTTONS_CLASSES = {
    'both': SourceButtons,
    'sources': SourceOnlyButtons,
    'content': MediaTypeButtons,
}


class MultiSearchController(ScriptWindowController):
    """Writes the multi search window from the skin's window file and shows it.

    The TMDbHelper discover sources for movies and tvshows follow the shortcut sources unless the skin passes the
    no_discover param. Their results use the widget style of the discover_style param.

    The skin can add list 200 to the window, which is filled with an item for all sources, each content type and each
    source that has results. The selected item decides which results are shown. Each item has the label and icon of
    its source and the target and widget_style properties. The skin passes the source_buttons param as sources or
    content for a source list with items for all sources and only each source or only each content type. The source
    list has both when the param is both or not passed. The param has no effect with the mediatype_lists param.

    The skin passes the mediatype_lists param for a window without the source list. Lists 501 to 510 each show
    the results of one content type, in the order of the content type buttons, alongside the list of all results.
    A content type list with the same results as the list of all results is hidden, and the
    SkinVariables.MultiSearch.Source.All.Label property gives the content type label for the skin to label the list
    of all results. Its sources button chooses between searching every source and searching one source instead of
    enabling any of the sources. The SkinVariables.MultiSearch.Sources.Label property gives All or the labels of the
    enabled sources for the skin to label the sources button.

    The skin passes the tmdbhelper_container param to set the TMDbHelper.WidgetContainer window property to the
    container of the visible list with the lowest id. TMDbHelper reads it from the window when the skin enables
    TMDbHelper.UseLocalWidgetContainer.

    The skin passes the no_all_list param alongside the mediatype_lists param for a window without the list of all
    results. The list of all results stays empty and no content type list is hidden, each one updating as each source
    finishes.

    The skin passes the progress_dialog param to show a background progress dialog while source lookups run or wait.
    """

    window_file_class = MultiSearchWindowFile
    window_class = MultiSearchWindow

    def __init__(
        self,
        menu=None,
        skin=None,
        paths_file=None,
        containers_file=None,
        limit=None,
        query=USE_STORED_QUERY,
        no_discover=False,
        discover_style=None,
        styles_file=None,
        source_buttons='both',
        mediatype_lists=False,
        tmdbhelper_container=False,
        no_all_list=False,
        progress_dialog=False,
    ):
        self.menu = menu
        self.skin = skin
        self.paths_file = paths_file
        self.containers_file = containers_file
        self.limit = limit
        self.query = query
        self.no_discover = no_discover
        self.discover_style = discover_style
        self.styles_file = styles_file
        self.source_buttons = source_buttons
        self.mediatype_lists = mediatype_lists
        self.tmdbhelper_container = tmdbhelper_container
        self.no_all_list = no_all_list
        self.progress_dialog = progress_dialog

    @cached_property
    def sources(self):
        return self.get_sources()

    def get_sources(self):
        if self.no_discover:
            return SearchSources(self.menu, self.skin, self.paths_file)
        return DiscoverSearchSources(self.menu, self.skin, self.paths_file, self.discover_style)

    @cached_property
    def mediatype_styles(self):
        return MediaTypeStyles(self.styles_file)

    @cached_property
    def containers(self):
        return ResultsContainers(self.containers_file, self.mediatype_styles)

    @cached_property
    def results_limit(self):
        return int(self.limit or RESULTS_LIMIT)

    @cached_property
    def progress(self):
        return self.get_progress()

    def get_progress(self):
        if self.progress_dialog:
            return SearchProgress()
        return NO_PROGRESS

    @cached_property
    def search(self):
        return MultiSearch(self.sources, self.results_limit, self.progress)

    @cached_property
    def stored_query(self):
        return StoredQuery(self.sources.menu)

    @cached_property
    def opening_query(self):
        """Search text the window opens with. The stored search unless the query param gives one or is empty."""
        return self.get_opening_query()

    def get_opening_query(self):
        if self.query is USE_STORED_QUERY:
            return self.stored_query.value
        return self.query or ''

    @cached_property
    def buttons(self):
        return self.get_buttons()

    def get_buttons(self):
        if self.mediatype_lists:
            return NoSourceListButtons(self.sources)
        return SOURCE_BUTTONS_CLASSES[self.source_buttons](self.sources)

    @cached_property
    def sources_picker(self):
        return self.get_sources_picker()

    def get_sources_picker(self):
        if self.mediatype_lists:
            return SingleSourcePicker(self.sources)
        return SourcesPicker(self.sources)

    @cached_property
    def has_source_list(self):
        """Whether the window file of every skin folder has the source list."""
        return all(window_file.template.has_source_list for window_file in self.window_files)

    @cached_property
    def source_list(self):
        return self.get_source_list()

    def get_source_list(self):
        if self.mediatype_lists or not self.has_source_list:
            return NoSourceList(self.buttons)
        return SourceList(self.buttons)

    @cached_property
    def lists(self):
        return self.get_lists()

    def get_lists(self):
        if self.mediatype_lists and self.no_all_list:
            return NoAllMediaTypeResultsLists(self.containers, self.buttons)
        if self.mediatype_lists:
            return MediaTypeResultsLists(self.containers, self.buttons)
        return ResultsLists(self.containers, self.buttons)

    @cached_property
    def widget_container(self):
        return self.get_widget_container()

    def get_widget_container(self):
        if self.tmdbhelper_container:
            return TMDbHelperWidgetContainer(self.lists)
        return WidgetContainer(self.lists)

    def get_window_file(self, folder):
        return MultiSearchWindowFile(folder, self.containers)

    def get_window_kwargs(self):
        return {
            'search': self.search,
            'buttons': self.buttons,
            'lists': self.lists,
            'widget_container': self.widget_container,
            'sources_picker': self.sources_picker,
            'source_list': self.source_list,
            'opening_query': self.opening_query,
            'stored_query': self.stored_query,
        }

    def get_result(self, window):
        # The window has closed so drop the queued searches and wait for the running searches.
        window.stop()


def run_multisearch(
    run_multisearch=None,
    menu=None,
    skin=None,
    paths=None,
    containers=None,
    limit=None,
    query=USE_STORED_QUERY,
    no_discover=False,
    discover_style=None,
    styles=None,
    source_buttons='both',
    mediatype_lists=False,
    tmdbhelper_container=False,
    no_all_list=False,
    progress_dialog=False,
    **kwargs,
):
    MultiSearchController(
        menu,
        skin,
        paths,
        containers,
        limit,
        query,
        no_discover,
        discover_style,
        styles,
        source_buttons,
        mediatype_lists,
        tmdbhelper_container,
        no_all_list,
        progress_dialog,
    ).run()
