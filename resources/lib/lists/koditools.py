# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import ListItem
from resources.lib.container import Container


class ListGetNumberSum(Container):
    def get_directory(self, expression, **kwargs):

        values = [0]
        values += [int(i) for i in expression.split() if i]

        items = [{
            'url': '',
            'listitem': ListItem(label=f'{sum(values)}', label2='', path='', offscreen=True),
            'isFolder': True}]

        self.add_items(items)


class ListGetSplitString(Container):
    def get_directory(self, values=None, infolabel=None, separator='|', **kwargs):
        from xbmc import getInfoLabel as get_infolabel
        values = get_infolabel(infolabel) if infolabel else values

        if not values:
            return

        items = [{
            'url': '',
            'listitem': ListItem(label=f'{i}', label2='', path='', offscreen=True),
            'isFolder': True} for i in values.split(separator) if i]

        self.add_items(items)


class ListGetEncodedString(Container):
    def get_directory(self, paths=None, window_prop=None, window_id=None, **kwargs):
        import xbmc
        from urllib.parse import quote_plus

        if not paths:
            return

        items = []
        for x, i in enumerate(paths):
            label = quote_plus(i)
            item = {
                'url': '',
                'listitem': ListItem(label=label, label2='', path='', offscreen=True),
                'isFolder': True}
            items.append(item)
            if not window_prop:
                continue
            if x == 0:
                xbmc.executebuiltin(f'SetProperty({window_prop},{label}{f",{window_id}" if window_id else ""})')
            xbmc.executebuiltin(f'SetProperty({window_prop}.{x},{label}{f",{window_id}" if window_id else ""})')

        self.add_items(items)


class ListGetFileExists(Container):
    def get_directory(self, paths, window_prop=None, window_id=None, **kwargs):

        import xbmc
        import xbmcvfs

        if not paths:
            return

        items = []
        for x, i in enumerate(paths):
            label = i
            path = i if xbmcvfs.exists(i) else ''
            item = {
                'url': path,
                'listitem': ListItem(label=label, label2='', path=path, offscreen=True),
                'isFolder': True}
            items.append(item)
            if not window_prop:
                continue
            if x == 0:
                xbmc.executebuiltin(f'SetProperty({window_prop},{path}{f",{window_id}" if window_id else ""})')
            xbmc.executebuiltin(f'SetProperty({window_prop}.{x},{path}{f",{window_id}" if window_id else ""})')

        self.add_items(items)
