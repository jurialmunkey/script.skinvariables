# -*- coding: utf-8 -*-
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from xbmcgui import ListItem, Dialog
from resources.lib.kodiutils import get_localized


SHORTCUT_CONFIG = 'skinvariables-shortcut-config.json'
SHORTCUT_FOLDER = 'special://skin/shortcuts/'
PLAYLIST_EXT = ('.xsp', '.m3u', '.m3u8', '.strm', '.wpl')
NO_FOLDER_ITEM = ('grouping://', 'plugin://script.skinvariables/?info=set_filter_dir')


def _ask_is_playable(path):
    return Dialog().yesno(
        get_localized(32050),  # Add playlist
        f'{path}\n{get_localized(32051)}',  # Add playlist as playable shortcut or browesable directory
        yeslabel=get_localized(208),  # Play
        nolabel=get_localized(1024)  # Browse
    )


class GetDirectoryBrowser():
    def __init__(self, use_details=True, item_prefix=None, use_rawpath=False, allow_links=True, folder_name=None):
        self.history = []
        self.filepath = f'{SHORTCUT_FOLDER}{SHORTCUT_CONFIG}'
        self.item_prefix = item_prefix or ''
        self.use_details = use_details
        self.use_rawpath = use_rawpath
        self.allow_links = allow_links
        self.folder_name = folder_name or f'{get_localized(32052)}...'
        self.heading_str = ''

    @cached_property
    def definitions(self):
        return self.get_definitions()

    def get_definitions(self):
        from resources.lib.shortcuts.futils import read_meta_from_file
        return read_meta_from_file(self.filepath)

    @staticmethod
    def get_formatted_path(path, node=None, link=True):
        if not path:
            return ('', '')
        if node and not link and path.endswith(PLAYLIST_EXT) and _ask_is_playable(path):
            return (f'PlayMedia({path})', '')
        # Links without nodes and folders with nodes retain the raw path.
        if (not node) is not (not link):
            return (path, node)
        if path.startswith('script://'):
            path = path.replace('script://', '')
            return (f'RunScript({path})', '')
        if path.startswith('androidapp://'):
            path = path.replace('androidapp://', '')
            return (f'StartAndroidActivity({path})', '')
        return (f'PlayMedia({path})', '')

    @staticmethod
    def get_decoded_reload(path):
        import re
        from urllib.parse import unquote_plus
        try:
            subs = re.search('&reload=(.*?)(&|$)', path)
            return path.replace(subs.group(0), unquote_plus(subs.group(0)))
        except AttributeError:
            return path

    def get_formatted_item(self, name, path, icon, node=None, link=True):
        if node == 'link':
            link = True
            node = ''
        path, target = self.get_formatted_path(path, node, link) if not self.use_rawpath else (
            self.get_decoded_reload(path),
            node,
        )
        item = {"label": name or '', "path": path or '', "icon": icon or '', "target": target or ''}
        return item

    def get_new_item(self, item, allow_browsing=True):
        from jurialmunkey.parser import boolean
        # Update to new item values
        icon = item[1].getArt('thumb') or ''
        node = item[1].getProperty('nodetype') or None
        name = item[1].getProperty('nodename') or item[1].getLabel() or ''
        link = not boolean(item[1].getProperty('isfolder') or False)
        path = item[0] or ''

        # If the item is a folder then we open it otherwise return formatted item
        if allow_browsing and item[2]:
            return self.get_directory(path, icon, name, item, True)
        return self.get_formatted_item(name, path, icon, node, link)

    def get_items(self, directory, path, icon, name, item, add_item=False):
        while True:
            directory_items = self.get_choices(directory, path, icon, name, item, add_item)
            self.heading_str = name or path
            index = Dialog().select(
                heading=self.heading_str,
                list=[entry[1] for entry in directory_items if entry],
                useDetails=self.use_details,
            )
            if index == -1:
                try:
                    directory, path, icon, name, item, add_item = self.history.pop()
                except IndexError:
                    return []
                continue
            item = directory_items[index]
            if not item[2]:
                return self.get_new_item(item, allow_browsing=False)
            self.history.append((directory, path, icon, name, item, True))
            child = item[1]
            location = self.get_location(
                item[0] or '',
                child.getArt('thumb') or '',
                child.getProperty('nodename') or child.getLabel() or '',
                item,
                True,
            )
            if location is None:
                return
            directory, path, icon, name, item, add_item = location

    def get_choices(self, directory, path, icon, name, item, add_item):
        choices = [entry for entry in directory.items if self.allow_links or entry[2]]
        if add_item and path and not path.startswith(NO_FOLDER_ITEM):
            listitem = ListItem(label=self.folder_name, label2=path, path=path, offscreen=True)
            listitem.setArt({'icon': icon, 'thumb': icon})
            listitem.setProperty('isfolder', 'True')
            listitem.setProperty('nodename', name)
            listitem.setProperty('nodetype', item[1].getProperty('nodetype') or '')
            choices.insert(0, (path, listitem, False))
        return choices

    def get_location(self, path='grouping://shortcuts/', icon='', name='Shortcuts', item=None, add_item=False):
        if not path:
            return

        from resources.lib.shortcuts.grouping import GetDirectoryGrouping
        DirectoryClass = GetDirectoryGrouping

        if not path.startswith('grouping://'):
            from resources.lib.shortcuts.jsonrpc import GetDirectoryJSONRPC
            DirectoryClass = GetDirectoryJSONRPC

        directory = DirectoryClass(
            path,
            definitions=self.definitions,
            target=item[1].getProperty('nodetype') if item else None,
        )
        if not directory.items and not add_item:
            return

        if not item:
            li = ListItem(label=name, label2=path, path=path, offscreen=True)
            li.setArt({'icon': icon, 'thumb': icon})
            li.setProperty('nodename', name)
            item = (path, li, True, )

        return directory, path, icon, name, item, add_item

    def get_directory(self, path='grouping://shortcuts/', icon='', name='Shortcuts', item=None, add_item=False):
        location = self.get_location(path, icon, name, item, add_item)
        if location is not None:
            return self.get_items(*location)
