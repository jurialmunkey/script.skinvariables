# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from xbmcgui import ListItem
from jurialmunkey.ftools import cached_property
from jurialmunkey.parser import parse_localize
from resources.lib.multisearch.results import SourceResults
from resources.lib.shortcuts.futils import read_meta_from_file
from resources.lib.shortcuts.node.controller import ListGetShortcutsNode


SEARCH_MENU = 'searchwidgets'
SEARCH_PATHS_FILE = 'special://skin/shortcuts/skinvariables-multisearch-paths.json'
SKINUSER_INFOLABEL = 'Skin.String(SkinVariables.SkinUser)'
TARGET_LIBRARIES = {
    'videos': 'video',
    'music': 'music',
}


class SearchSource:
    """Search widget from the shortcuts file. Keeps the results of each query it has looked up.

    The path is either a name defined in the skin's search paths file or a raw path.
    """

    def __init__(self, index, meta, definitions):
        self.index = index
        self.meta = meta
        self.definitions = definitions
        self.cache = {}

    @cached_property
    def label(self):
        return parse_localize(self.meta.get('label') or '')

    @cached_property
    def icon(self):
        return self.meta.get('icon') or ''

    @cached_property
    def target(self):
        return self.meta.get('target') or ''

    @cached_property
    def widget_style(self):
        return self.meta.get('widget_style') or ''

    @cached_property
    def library(self):
        return TARGET_LIBRARIES.get(self.target)

    @cached_property
    def template(self):
        return self.get_template()

    def get_template(self):
        path = self.meta['path']
        return self.definitions.get(path, path)

    @property
    def listitem(self):
        return self.get_listitem()

    def get_listitem(self):
        listitem = ListItem(label=self.label, offscreen=True)
        listitem.setArt({'icon': self.icon, 'thumb': self.icon})
        return listitem

    def get_results(self, query, limit):
        try:
            return self.cache[query.raw]
        except KeyError:
            self.cache[query.raw] = SourceResults(self, query, limit).items
            return self.cache[query.raw]


class SearchSources:
    """Search widgets of a shortcuts menu and which of them are enabled. All are enabled when the window opens."""

    def __init__(self, menu=None, skin=None, paths_file=None):
        self.menu = menu or SEARCH_MENU
        self.skin = skin
        self.paths_file = paths_file or SEARCH_PATHS_FILE
        self.disabled_positions = set()

    @cached_property
    def skinid(self):
        """Shortcuts folder of the skin, matching the generator's skin id for the current skin user."""
        return self.get_skinid()

    def get_skinid(self):
        skinid = self.skin or xbmc.getSkinDir()
        skinuser = xbmc.getInfoLabel(SKINUSER_INFOLABEL)
        return f'{skinid}-{skinuser}' if skinuser else skinid

    @cached_property
    def definitions(self):
        """Paths by name from the skin. Skins without the file only offer sources with raw paths."""
        return self.get_definitions()

    def get_definitions(self):
        return read_meta_from_file(self.paths_file) or {}

    @cached_property
    def menu_meta(self):
        return self.get_menu_meta()

    def get_menu_meta(self):
        directory = ListGetShortcutsNode(None, None)
        return directory.get_directory(menu=self.menu, skin=self.skinid, func='node') or []

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        return [
            SearchSource(index, meta, self.definitions)
            for index, meta in enumerate(self.menu_meta)
            if meta.get('path')
        ]

    @property
    def enabled_positions(self):
        return [
            position
            for position in range(len(self.items))
            if position not in self.disabled_positions
        ]

    def set_enabled_positions(self, positions):
        self.disabled_positions = set(range(len(self.items))) - set(positions)

    @property
    def enabled(self):
        return [self.items[position] for position in self.enabled_positions]

    @property
    def listitems(self):
        return [source.listitem for source in self.items]
