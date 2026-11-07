# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import resources.lib.shortcuts.futils as shortcutfutils
from resources.lib.shortcuts.node.constants import CONTEXTMENU_BASIC, CONTEXTMENU_MAINMENU, CONTEXTMENU_CONFIGFILE


class FormatDict(dict):
    def __missing__(self, key):
        if 'listitem_obj' in self.keys():
            return self['listitem_obj'].getProperty(key)
        return ''


class ContextMenuDict(dict):
    def __getitem__(self, key):
        if key != 'basic':  # Basic menu should be appended to all other types
            return dict.__getitem__(self, 'basic') + dict.__getitem__(self, key)
        return dict.__getitem__(self, key)

    def __missing__(self, key):
        if key == 'basic':
            return CONTEXTMENU_BASIC
        if key == 'mainmenu':
            return CONTEXTMENU_MAINMENU
        return []


def get_contextmenu_config():
    return ContextMenuDict(shortcutfutils.read_meta_from_file(CONTEXTMENU_CONFIGFILE) or {})


def get_contextmenu(node, mode='submenu'):
    contextmenu = get_contextmenu_config()
    if not node:
        return contextmenu['mainmenu']
    if mode == 'widgets':
        return contextmenu['widgets']
    return contextmenu['basic']
