# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.multisearch.buttons import SourceButtons
from resources.lib.multisearch.search import MultiSearch, RESULTS_LIMIT
from resources.lib.multisearch.sources import SearchSources
from resources.lib.multisearch.template import MultiSearchWindowFile
from resources.lib.multisearch.window import MultiSearchWindow
from resources.lib.scriptwindow.controller import ScriptWindowController


class MultiSearchController(ScriptWindowController):
    """Writes the multi search window from the skin's window file and shows it."""

    window_file_class = MultiSearchWindowFile
    window_class = MultiSearchWindow

    def __init__(self, menu=None, skin=None, paths_file=None, limit=None):
        self.menu = menu
        self.skin = skin
        self.paths_file = paths_file
        self.limit = limit

    @cached_property
    def sources(self):
        return SearchSources(self.menu, self.skin, self.paths_file)

    @cached_property
    def results_limit(self):
        return int(self.limit or RESULTS_LIMIT)

    @cached_property
    def search(self):
        return MultiSearch(self.sources, self.results_limit)

    @cached_property
    def buttons(self):
        return SourceButtons(self.sources)

    def get_window_file(self, folder):
        return MultiSearchWindowFile(folder, self.buttons)

    def get_window_kwargs(self):
        return {'search': self.search, 'buttons': self.buttons}

    def get_result(self, window):
        # The window has closed so stop the queued search and wait for the running search.
        window.stop()


def run_multisearch(run_multisearch=None, menu=None, skin=None, paths=None, limit=None, **kwargs):
    MultiSearchController(menu, skin, paths, limit).run()
