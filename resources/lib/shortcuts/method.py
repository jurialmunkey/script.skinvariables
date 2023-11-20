import xbmc
import xbmcgui
from jurialmunkey.parser import parse_localize
from resources.lib.shortcuts.node import ListGetShortcutsNode


LISTITEM_VALUE_PAIRS = (('label', 'Label'), ('icon', 'Icon'), ('path', 'FolderPath'))
LISTITEM_NOTFOUND_HEADING = 'No path'
LISTITEM_NOTFOUND_MESSAGE = 'No item path found!'
NODE_SELECT_HEADING = 'Choose menu'
MODE_SELECT_HEADING = 'Choose mode'
NODE_ADDITEM_LABEL = 'Add here...'
DEFAULT_MODES = ('submenu', 'widgets')


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


class MenuNode():
    def __init__(self, skin, menufiles=None):
        self.skin = skin
        self.menufiles = menufiles or []

    def select_menu(self):
        if not self.menufiles:
            return
        x = xbmcgui.Dialog().select(NODE_SELECT_HEADING, self.menufiles)
        if x == -1:
            return
        return self.menufiles[x]

    def get_menu(self):
        self._menu = self.select_menu()
        return self._menu

    @property
    def menu(self):
        try:
            return self._menu
        except AttributeError:
            return self.get_menu()

    def select_node(self, mode, guid):
        lgsn = ListGetShortcutsNode(-1, '')
        lgsn.get_directory(menu=self.menu, skin=self.skin, item=None, mode=mode, guid=guid, func='node')
        if lgsn.menunode is None:
            return
        x = xbmcgui.Dialog().select(NODE_SELECT_HEADING, [parse_localize(i.get('label') or '') for i in lgsn.menunode] + [NODE_ADDITEM_LABEL])
        if x == -1:
            return
        if x == len(lgsn.menunode):
            return lgsn
        y = xbmcgui.Dialog().select(MODE_SELECT_HEADING, DEFAULT_MODES)
        if y == -1:
            return self.select_node(mode, guid)
        return self.select_node(DEFAULT_MODES[y], lgsn.menunode[x].get('guid'))

    def set_item_to_node(self, item):
        lgsn = self.select_node('submenu', None)
        if not lgsn:
            return
        lgsn.menunode.append(item)
        lgsn.write_meta_to_file()
        lgsn.do_refresh()


def set_listitem_to_menunode(set_listitem_to_menunode, skin, label=None, icon=None, path=None, target=None, use_listitem=True):
    if not set_listitem_to_menunode or not skin:
        return
    item = {'label': label, 'icon': icon, 'path': path, 'target': target}

    if use_listitem:
        item = get_item_from_listitem(item)
        item['target'] = get_target_from_window() or target or 'videos'

    if not item['path']:
        xbmcgui.Dialog().ok(heading=LISTITEM_NOTFOUND_HEADING, message=LISTITEM_NOTFOUND_MESSAGE)
        return

    MenuNode(skin, menufiles=set_listitem_to_menunode.split('||')).set_item_to_node(item)


def set_shortcut(set_shortcut):
    import xbmc
    from jurialmunkey.window import WindowProperty
    from resources.lib.shortcuts.browser import GetDirectoryBrowser

    with WindowProperty(('IsSkinShortcut', 'True')):
        item = GetDirectoryBrowser(return_item=True).get_directory()

    if not item:
        return

    item = {f'{set_shortcut}.{k}': v for k, v in item.items()}

    for k, v in item.items():
        if not isinstance(v, str):
            continue
        xbmc.executebuiltin(f'Skin.SetString({k},{v})')
