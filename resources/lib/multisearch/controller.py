# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.kodiutils import ADDON
from resources.lib.multisearch.search import MultiSearch, RESULTS_LIMIT
from resources.lib.multisearch.sources import SearchSources
from resources.lib.multisearch.window import MultiSearchWindow


class MultiSearchController:
    """Opens the multi search window from the skin's window file.

    The window is not generated so the skin provides script-skinvariables-multisearch.xml in its skin folders.
    """

    filename = 'script-skinvariables-multisearch.xml'

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
    def scriptpath(self):
        return ADDON.getAddonInfo('path')

    def get_window(self):
        return MultiSearchWindow(self.filename, self.scriptpath, 'Default', '1080i', search=self.search)

    def run(self):
        window = self.get_window()
        window.doModal()
        window.stop()
        del window


def run_multisearch(run_multisearch=None, menu=None, skin=None, paths=None, limit=None, **kwargs):
    MultiSearchController(menu, skin, paths, limit).run()
