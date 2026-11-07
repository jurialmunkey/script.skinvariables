# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import resources.lib.shortcuts.futils as shortcutfutils
from jurialmunkey.litems import ContainerDirectory
from jurialmunkey.parser import boolean
from resources.lib.filters.parameters import get_filters
from resources.lib.shortcuts.node.constants import SKIN_DIR
from resources.lib.shortcuts.node.tree import get_default_item, get_nodename, assign_guid
from resources.lib.shortcuts.node.storage import cache_meta_from_file
from resources.lib.shortcuts.node.properties import NodeProperties
from resources.lib.shortcuts.node.items import NodeDirectoryItems
from resources.lib.shortcuts.node.actions.methods import NodeMethods
from resources.lib.shortcuts.node.actions.submenus import NodeSubmenuMethods


class ListGetShortcutsNode(ContainerDirectory, NodeProperties, NodeMethods, NodeSubmenuMethods):
    refresh = False
    update_listing = False

    def get_url(self, x, node_name=None):
        url = (
            f'plugin://script.skinvariables/?info=get_shortcuts_node&menu={self.menu}'
            f'&skin={self.skin}&mode={self.mode}&item={x}'
        )
        url = url if not self.node else f'{url}&node={node_name or get_nodename(self.node)}'
        url = url if not self.guid else f'{url}&guid={self.guid}'
        return url

    def get_meta(self, refresh=False, restore=False):
        if not self.filepath:
            return
        meta = cache_meta_from_file(self.filepath, fileprop=self.fileprop, refresh=refresh) if not restore else None
        if meta is None:
            meta = cache_meta_from_file(f'{SKIN_DIR}{self.filename}', fileprop=self.fileprop, refresh=refresh)
            if meta is not None:
                shortcutfutils.write_meta_to_file(
                    meta,
                    folder=self.skin,
                    filename=self.filename,
                    fileprop=self.fileprop,
                )
        return meta

    def write_meta_to_file(self, reload=True):
        shortcutfutils.write_meta_to_file(
            assign_guid(self.meta),
            folder=self.skin,
            filename=self.filename,
            fileprop=self.fileprop,
            reload=reload,
        )

    def get_directory_items(self, blank=False, filters=None):
        return NodeDirectoryItems(self, blank, filters).items

    def get_directory(
        self,
        menu=None,
        skin=None,
        item=None,
        node=None,
        mode=None,
        func=None,
        guid=None,
        edit=None,
        noblank=None,
        **kwargs,
    ):
        self.menu = menu
        self.skin = skin
        self.mode = mode
        self.guid = guid
        self.node = node
        self.item = item
        self.edit = edit

        if func == 'node':
            return self.menunode

        if (self.item is None or not self.meta) and func in (None, 'list'):
            return self.list_directory(func, noblank, kwargs)

        item_func = getattr(self, func)

        if not self.meta and self.filepath:
            self._meta = [get_default_item()]

        path_partitions = [i.partition('::') if i else ('', '', '', ) for i in self.params.get('paths', [])]
        path_args = [k for k, s, v in path_partitions if not s]
        path_kwargs = {k: v for k, s, v in path_partitions if s}
        item_func(*path_args, **path_kwargs)  # If an item is specified we do its function

    def list_directory(self, func, noblank, kwargs):
        use_blank = self.edit and not boolean(noblank)
        blank = True if not self.menunode and use_blank else False
        items = self.get_directory_items(blank=blank, filters=get_filters(**kwargs))
        if func == 'list':
            return items
        if not items and use_blank:  # If we didn't get any items from filter and we're in edit mode then get blank
            items = self.get_directory_items(blank=True)
        return self.add_items(items, update_listing=self.update_listing)
