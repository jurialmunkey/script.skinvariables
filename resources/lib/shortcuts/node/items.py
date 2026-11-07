# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import ListItem
from jurialmunkey.ftools import cached_property
from jurialmunkey.parser import boolean, parse_localize
from resources.lib.filters.items import is_excluded
from resources.lib.kodiutils import get_localized
from resources.lib.shortcuts.node.context import FormatDict, get_contextmenu_config
from resources.lib.shortcuts.node.tree import get_nodename


class NodeListItem:
    def __init__(self, directory, index, source, contextmenu, blank=False, filters=None):
        self.directory = directory
        self.index = index
        self.source = source
        self.contextmenu = contextmenu
        self.blank = blank
        self.filters = filters

    @cached_property
    def node_name(self):
        return self.get_node_name()

    def get_node_name(self):
        return get_nodename(self.directory.node)

    @cached_property
    def url(self):
        return self.get_url()

    def get_url(self):
        return self.directory.get_url(self.index, self.node_name)

    @cached_property
    def metadata(self):
        return self.get_metadata()

    def get_metadata(self):
        item = self.source
        item['item'] = str(self.index)
        item['node'] = self.node_name if self.directory.node else ''
        item['list'] = f'{self.node_name}.{self.index}' if self.directory.node else str(self.index)
        item.update({key: str(getattr(self.directory, key) or '') for key in ('menu', 'skin', 'mode', 'name')})
        self.submenu = item.pop('submenu', [])
        self.widgets = item.pop('widgets', [])
        return item

    @cached_property
    def included(self):
        return self.get_included()

    def get_included(self):
        metadata = self.metadata
        if self.blank or not self.filters:
            return True
        return all(not is_excluded({'infolabels': metadata}, **rule) for rule in self.filters.values())

    @cached_property
    def label(self):
        return self.get_label()

    def get_label(self):
        return parse_localize(self.metadata.pop('label', ''))

    @cached_property
    def icon(self):
        return self.get_icon()

    def get_icon(self):
        return self.metadata.pop('icon', '')

    @cached_property
    def path(self):
        return self.get_path()

    def get_path(self):
        return self.metadata.get('path', '')

    @cached_property
    def target(self):
        return self.get_target()

    def get_target(self):
        return self.metadata.get('target', '')

    @cached_property
    def format_mapping(self):
        return self.get_format_mapping()

    def get_format_mapping(self):
        mapping = {'label': self.label, 'path': self.path, 'icon': self.icon, 'name': self.label, 'target': self.target}
        mapping.update(self.metadata)
        return FormatDict(mapping)

    def get_context_entry(self, label, action, params):
        command = f'RunPlugin({self.url}&func={action}{"&&" if params else ""}{"&&".join(params)})'
        return label.format_map(self.format_mapping), command.format_map(self.format_mapping)

    @cached_property
    def context_entries(self):
        return self.get_context_entries()

    def get_context_entries(self):
        entries = self.contextmenu['mainmenu' if not self.directory.node else 'basic']
        return [self.get_context_entry(*entry) for entry in entries]

    @cached_property
    def listitem(self):
        return self.get_listitem()

    def get_listitem(self):
        item = ListItem(label=self.label, label2='', path=self.path, offscreen=True)
        item.setArt({'icon': self.icon, 'thumb': self.icon})
        item.setProperties({key: value for key, value in self.metadata.items() if key and value})
        if not self.target:
            item.setProperty('isPlayable', 'True')
        item.setProperty('target', self.target)
        item.setProperty('url', self.url)
        item.setProperty('label', self.label)
        if self.submenu:
            item.setProperty('hasSubmenu', 'True')
        if self.widgets:
            item.setProperty('hasWidgets', 'True')
        item.addContextMenuItems(self.context_entries)
        return item

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        if (not self.source or boolean(self.source.get('disabled'))) and not self.blank and not self.directory.edit:
            return
        if not self.included:
            return
        item = self.listitem
        guid = self.metadata.get('guid', '')
        path = f'{self.path}#guid={guid}' if self.directory.edit and guid else self.path
        return path, item, bool(self.target)


class NodeDirectoryItems:
    def __init__(self, directory, blank=False, filters=None):
        self.directory = directory
        self.blank = blank
        self.filters = filters

    @cached_property
    def contextmenu(self):
        return self.get_contextmenu()

    def get_contextmenu(self):
        return get_contextmenu_config()

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        contextmenu = self.contextmenu
        if self.blank:
            source = {'label': get_localized(32078), 'blank': 'True'}
            return [NodeListItem(self.directory, 0, source, contextmenu, blank=True).result]
        items = (
            NodeListItem(self.directory, index, source, contextmenu, filters=self.filters).result
            for index, source in enumerate(self.directory.menunode or [])
        )
        return [item for item in items if item]
