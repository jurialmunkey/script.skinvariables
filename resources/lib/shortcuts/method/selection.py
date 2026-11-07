# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
import xbmc
import xbmcgui
from resources.lib.kodiutils import get_localized


def get_target_from_window():
    if xbmc.getCondVisibility('Window.IsVisible(MyVideoNav.xml)'):
        return 'videos'
    if xbmc.getCondVisibility('Window.IsVisible(MyMusicNav.xml)'):
        return 'music'
    if xbmc.getCondVisibility('Window.IsVisible(MyPics.xml)'):
        return 'pictures'
    if xbmc.getCondVisibility('Window.IsVisible(MyPrograms.xml)'):
        return 'programs'
    if xbmc.getCondVisibility('Window.IsVisible(MyPVRGuide.xml)'):
        return 'tvguide'
    if xbmc.getCondVisibility('Window.IsVisible(MyPVRChannels.xml)'):
        return 'tvchannels'


def get_item_from_listitem(item=None, value_pairs=None, listitem='Container.ListItem'):
    item = item or {}
    value_pairs = value_pairs or LISTITEM_VALUE_PAIRS
    return {k: xbmc.getInfoLabel(f'{listitem}.{v}') or item.get(k) or '' for k, v in value_pairs}


LISTITEM_VALUE_PAIRS = (('label', 'Label'), ('icon', 'Icon'), ('path', 'FolderPath'))
DEFAULT_MODES = ('submenu', 'widgets')


class MenuNode():
    def __init__(self, skin, menufiles=None, levels=1):
        self.skin = skin
        self.menufiles = menufiles or []
        self.levels = int(levels)

    def select_menu(self):
        if not self.menufiles:
            return
        x = xbmcgui.Dialog().select(get_localized(32069), self.menufiles)
        if x == -1:
            return
        return self.menufiles[x]

    def get_menu(self):
        self._menu = self.select_menu()
        return self._menu

    @cached_property
    def menu(self):
        return self.get_menu()

    def select_node(self, mode, guid, level=0):
        while True:
            from resources.lib.shortcuts.node.controller import ListGetShortcutsNode
            lgsn = ListGetShortcutsNode(-1, '')
            lgsn.get_directory(menu=self.menu, skin=self.skin, item=None, mode=mode, guid=guid, func='node')
            if lgsn.menunode is None:
                return
            choices = [f'{get_localized(32071)}...']
            if level < self.levels:
                from jurialmunkey.parser import parse_localize
                choices = [parse_localize(i.get('label') or '') for i in lgsn.menunode] + choices
            x = xbmcgui.Dialog().select(get_localized(32069), choices)
            if x == -1:
                return
            if choices[x] == f'{get_localized(32071)}...':
                return lgsn
            y = xbmcgui.Dialog().select(get_localized(32070), DEFAULT_MODES)
            if y == -1:
                continue
            mode, guid, level = DEFAULT_MODES[y], lgsn.menunode[x].get('guid'), level + 1

    def set_item_to_node(self, item):
        lgsn = self.select_node('submenu', None)
        if not lgsn:
            return
        lgsn.menunode.append(item)
        lgsn.write_meta_to_file()
        lgsn.do_refresh()
