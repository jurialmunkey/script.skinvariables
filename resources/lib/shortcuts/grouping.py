# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import ListItem
from jurialmunkey.parser import boolean
from resources.lib.kodiutils import ProgressDialog
from xbmc import getCondVisibility
from resources.lib.shortcuts.common import GetDirectoryCommon
from resources.lib.kodiutils import get_localized


class GetDirectoryGrouping(GetDirectoryCommon):
    def get_directory(self):
        if not self.path:
            return []
        try:
            return self.definitions[self.path]
        except KeyError:
            return []

    def get_item(self, i):
        if i.get('rule') and not getCondVisibility(i['rule']):
            return
        listitem = ListItem(label=i['name'], label2=i['path'], path=i['path'], offscreen=True)
        listitem.setArt({'icon': i['icon'], 'thumb': i['icon']})
        listitem_isfolder = True
        listitem_nodetype = i.get('node') or self.target or ''
        if boolean(i['link']):
            listitem_nodetype = 'link'
            listitem_isfolder = False
        listitem.setProperty('nodetype', listitem_nodetype)
        item = (i['path'], listitem, listitem_isfolder, )
        return item

    def get_items(self):
        with ProgressDialog(
            'Skin Variables',
            f'{get_localized(32053)}...\n{self.path}',
            total=1,
            logging=2,
            background=False,
        ):
            if not self.directory:
                return []
            return [item for entry in self.directory if entry for item in self.get_entry_items(entry) if item]

    def get_entry_items(self, entry):
        if isinstance(entry, dict):
            return [self.get_item(entry)]
        if '://' not in entry:
            return []
        directory_class = GetDirectoryGrouping
        if not entry.startswith('grouping://'):
            from resources.lib.shortcuts.jsonrpc import GetDirectoryJSONRPC
            directory_class = GetDirectoryJSONRPC
        directory = directory_class(entry, definitions=self.definitions, target=self.target)
        return directory.get_items() or []
