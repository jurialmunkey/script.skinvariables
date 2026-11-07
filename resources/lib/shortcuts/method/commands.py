# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import xbmcgui
from resources.lib.kodiutils import get_localized
from resources.lib.shortcuts.method.selection import get_item_from_listitem, get_target_from_window, MenuNode


def set_listitem_to_menunode(
    set_listitem_to_menunode,
    skin,
    label=None,
    icon=None,
    path=None,
    target=None,
    use_listitem=True,
):
    if not set_listitem_to_menunode or not skin:
        return
    item = {'label': label, 'icon': icon, 'path': path, 'target': target}

    if use_listitem:
        item = get_item_from_listitem(item)
        item['target'] = get_target_from_window() or target or 'videos'

    if not item['path']:
        xbmcgui.Dialog().ok(heading=get_localized(32068), message=get_localized(32067))
        return

    MenuNode(skin, menufiles=set_listitem_to_menunode.split('||')).set_item_to_node(item)


def set_shortcut(set_shortcut, use_rawpath=False):
    import xbmc
    from jurialmunkey.parser import boolean
    from jurialmunkey.window import WindowProperty
    from resources.lib.shortcuts.browser import GetDirectoryBrowser

    with WindowProperty(('IsSkinShortcut', 'True')):
        item = GetDirectoryBrowser(use_rawpath=boolean(use_rawpath)).get_directory()

    if not item:
        return

    item = {f'{set_shortcut}.{k}': v for k, v in item.items()}

    for k, v in item.items():
        if not isinstance(v, str):
            continue
        xbmc.executebuiltin(f'Skin.SetString({k},{v})')
