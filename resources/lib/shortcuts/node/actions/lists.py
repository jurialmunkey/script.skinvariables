# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.shortcuts.node.actions.batches import NodeListAddition, NodeListDeletion
from xbmcgui import Dialog
from resources.lib.kodiutils import get_localized
from resources.lib.shortcuts.node.constants import GROUPING_DEFAULT
from resources.lib.shortcuts.node.directory import GetDirectoryItems


class ListsMethods:
    def do_list_del(self, grouping=GROUPING_DEFAULT, use_rawpath=False, **kwargs):
        directory_item_getter = GetDirectoryItems(
            grouping=grouping,
            use_rawpath=use_rawpath,
            folder_name='Delete list...',
        )
        items = directory_item_getter.items or []
        index = NodeListDeletion(self.menunode, items, kwargs).result

        if not index:
            Dialog().ok(get_localized(32087), get_localized(32089))
            return
        if not Dialog().yesno(get_localized(32087), get_localized(32088).format(item_count=len(index))):
            return
        for x in sorted(index, reverse=True):
            del self.menunode[x]
        self.write_meta_to_file()

    def do_list_add(self, grouping=GROUPING_DEFAULT, use_rawpath=False, item_limit=30, **kwargs):
        """
        Choose a list to add multiple items automatically
        Specific kwargs as additional properties to add to items
        """
        x = int(self.item)
        item_limit = int(item_limit)

        directory_item_getter = GetDirectoryItems(grouping=grouping, use_rawpath=use_rawpath, folder_name='Add list...')
        items = directory_item_getter.items
        if not items:
            Dialog().ok(get_localized(32083), get_localized(32085))
            return
        directory_jsonrpc_items = directory_item_getter.directory_jsonrpc.items

        items = NodeListAddition(self.menunode, items, kwargs).result

        if len(items) < 1:
            Dialog().ok(get_localized(32083), get_localized(32085))
            return

        if len(items) > item_limit:
            Dialog().ok(get_localized(32083), get_localized(32086).format(item_count=len(items), item_limit=item_limit))
            return

        message = get_localized(32084).format(
            item_count=len(items),
            skip_count=len(directory_jsonrpc_items) - len(items),
        )
        if not Dialog().yesno(get_localized(32083), message):
            return

        for y, item in enumerate(items):
            self.menunode.insert(x + y + 1, item)  # Add enumerator to original position to insert in order

        self.write_meta_to_file()
