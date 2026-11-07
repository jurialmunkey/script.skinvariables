# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import ListItem, Dialog
from jurialmunkey.parser import boolean
from resources.lib.kodiutils import get_localized
from resources.lib.shortcuts.node.tree import get_menunode_item


class NavigationMethods:
    def get_menunode_item(self, x):
        return get_menunode_item(self.menunode, x)

    def do_refresh(self, restore=False, executebuiltin=None):
        restore = boolean(restore)
        if restore and not Dialog().yesno(get_localized(32081), f'{get_localized(32082)}\n{get_localized(32043)}'):
            return
        self._meta = self.get_meta(refresh=True, restore=restore)
        self.do_rebuild(dialog=False, executebuiltin=executebuiltin)

    def do_rebuild(self, dialog=True, executebuiltin=None):
        if dialog and not Dialog().yesno(get_localized(32079), get_localized(32080)):
            return
        self.write_meta_to_file(reload=False)
        from resources.lib.script import Script
        Script(paramstring=f'action=buildtemplate&force').run()
        if not executebuiltin:
            return
        import xbmc
        xbmc.Monitor().waitForAbort(0.4)
        xbmc.executebuiltin(executebuiltin)

    def do_open(self):
        x = int(self.item)
        path = self.get_menunode_item(x).get('path')
        target = self.get_menunode_item(x).get('target')
        if not path:
            return
        import xbmc
        import xbmcplugin
        xbmcplugin.setResolvedUrl(self.handle, False, ListItem())
        xbmc.Monitor().waitForAbort(0.2)
        xbmc.executebuiltin('ActivateWindow({target},{path},return)' if target else path)

    def do_executebuiltin(self, *args):
        if not args:
            return
        import xbmc
        for i in args:
            xbmc.executebuiltin(i)

    def do_windowprop(self, window_prop, x, window_id=None):
        import xbmc
        if not window_prop or x is None:
            return
        window_id = '' if not window_id else f',{window_id}'
        xbmc.executebuiltin(f'SetProperty({window_prop},{self.get_url(x)}{window_id})')

    @staticmethod
    def do_refocus(refocus, x, sleep=0.2):
        import xbmc
        if not refocus or x is None:
            return
        xbmc.Monitor().waitForAbort(sleep)  # Wait a moment before refocusing to make sure has updated
        xbmc.executebuiltin(f'SetFocus({refocus},{x},absolute)')
