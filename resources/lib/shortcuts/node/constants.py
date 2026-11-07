# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import resources.lib.shortcuts.futils as shortcutfutils
from resources.lib.kodiutils import get_localized


FILE_PREFIX = shortcutfutils.FILE_PREFIX

ICON_DIR = 'special://skin/extras/icons/'
SKIN_DIR = 'special://skin/shortcuts/'
CONTEXTMENU_CONFIGFILE = f'{SKIN_DIR}/skinvariables-shortcut-context.json'
ICON_FOLDER = f'{ICON_DIR}folder.png'
ICON_ADD = f'{ICON_DIR}circle-plus.png'
ICON_WIDGET = f'{ICON_DIR}shapes.png'
GROUPING_DEFAULT = 'grouping://shortcuts/'


CONTEXTMENU_BASIC = [
    [get_localized(32090), "do_choose", []],
    [get_localized(15217), "do_action", []],
    [get_localized(118), "do_edit", ["label"]],
    [get_localized(32077), "do_icon", []],
    [get_localized(13332), "do_move", ["-1"]],
    [get_localized(13333), "do_move", ["1"]],
    [get_localized(115), "do_copy", []],
    [get_localized(117), "do_delete", []],
    [get_localized(32091), "do_refresh", []],
]


CONTEXTMENU_MAINMENU = [
    [get_localized(32081), "do_refresh", ["True"]],
    [get_localized(32092), "do_submenu", []],
    [get_localized(32093), "do_widgets", []],
]
