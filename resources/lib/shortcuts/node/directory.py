# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from jurialmunkey.parser import boolean
from resources.lib.shortcuts.node.constants import GROUPING_DEFAULT


class GetDirectoryItems():
    def __init__(self, grouping=GROUPING_DEFAULT, use_rawpath=False, folder_name=None):
        self.grouping = grouping
        self.use_rawpath = use_rawpath
        self.folder_name = folder_name

    @cached_property
    def directory_browser(self):
        return self.get_directory_browser()

    def get_directory_browser(self):
        from resources.lib.shortcuts.browser import GetDirectoryBrowser
        return GetDirectoryBrowser(use_rawpath=True, allow_links=False, folder_name=self.folder_name)

    @cached_property
    def directory_jsonrpc(self):
        return self.get_directory_jsonrpc()

    def get_directory_jsonrpc(self):
        from resources.lib.shortcuts.jsonrpc import GetDirectoryJSONRPC
        return GetDirectoryJSONRPC(
            self.item_folder['path'],
            definitions=self.directory_browser.definitions,
            target=self.item_folder['target'],
        )

    @cached_property
    def item_folder(self):
        return self.get_item_folder()

    @cached_property
    def items(self):
        return self.get_items()

    def get_item_folder(self):
        from jurialmunkey.window import WindowProperty
        with WindowProperty(('IsSkinShortcut', 'True')):
            self._item_folder = self.directory_browser.get_directory(path=self.grouping)
        return self._item_folder

    def get_items(self):
        if not self.item_folder:
            return

        if not self.directory_jsonrpc.items:
            return

        if not boolean(self.use_rawpath):
            self.directory_browser.use_rawpath = False
            self.directory_browser.allow_links = True

        return (self.get_item(item) for item in self.directory_jsonrpc.items)

    def get_item(self, item):
        item[1].setProperty('isfolder', 'True' if item[2] else 'False')
        return self.directory_browser.get_new_item(item, allow_browsing=False)
