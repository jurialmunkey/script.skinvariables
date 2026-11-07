# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import Dialog
from jurialmunkey.ftools import cached_property
from resources.lib.viewtypes.common import ADDON
from resources.lib.viewtypes.items import ViewTypesItem, ViewTypesGroup


class ViewTypesPluginGroup:
    def __init__(self, items, groups=None, header=None):
        self.items = items
        self.groups = groups
        self.header = header or ''

    def get_valid_viewtypes(self, group):
        return tuple(item for item in self.items if item.view_id in group['viewtypes'])

    @cached_property
    def configured_groups(self):
        return self.get_configured_groups()

    def get_configured_groups(self):
        groups = (
            ViewTypesGroup(key, self.get_valid_viewtypes(group), group.get('icon'))
            for key, group in self.groups.items()
        )
        return tuple(group for group in groups if group.items)

    @cached_property
    def choice(self):
        return self.get_choice()

    def get_choice(self):
        from resources.lib.kodiutils import isactive_winprop
        with isactive_winprop('SkinViewtypes.DialogIsActive', reverse=True):
            return self.select()

    def select(self):
        index = Dialog().select(self.header, [group.item for group in self.configured_groups], useDetails=True)
        if index == -1:
            return
        return self.configured_groups[index]


class ViewTypesPluginView:
    def __init__(self, viewtypes_obj, contentid, pluginname):
        self.viewtypes_obj = viewtypes_obj
        self.contentid = contentid
        self.pluginname = pluginname

    @cached_property
    def current_viewid(self):
        return self.get_current_viewid()

    def get_current_viewid(self):
        try:
            return self.viewtypes_obj.addon_meta[self.pluginname][self.contentid]
        except (KeyError, TypeError):
            return

    @cached_property
    def preselect(self):
        return self.get_preselect()

    def get_preselect(self):
        if not self.current_viewid or self.current_viewid not in self.viewtype_ids:
            return
        return self.viewtype_ids.index(self.current_viewid)

    @cached_property
    def content(self):
        return self.get_content()

    def get_content(self):
        return self.viewtypes_obj.rules.get(self.contentid)

    @cached_property
    def content_viewtypes(self):
        return self.get_content_viewtypes()

    def get_content_viewtypes(self):
        return self.content.get('viewtypes') or []

    @cached_property
    def viewtype_ids(self):
        return self.get_viewtype_ids()

    def get_viewtype_ids(self):
        return [viewid for viewid in self.viewtypes_obj.viewtypes if viewid in self.content_viewtypes]

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        items = tuple(self.get_viewtypes_item(viewid) for viewid in self.viewtype_ids)
        if not self.viewtypes_obj.groups:
            return items
        choice = ViewTypesPluginGroup(items, self.viewtypes_obj.groups, header=self.header).choice
        return choice.items if choice else None

    def get_viewtypes_item(self, view_id):
        return ViewTypesItem(self.viewtypes_obj.viewtypes, view_id, self.viewtypes_obj.icons)

    @cached_property
    def header(self):
        return self.get_header()

    def get_header(self):
        return f'{ADDON.getLocalizedString(32004)} {self.pluginname} ({self.contentid})'

    @cached_property
    def choice(self):
        return self.get_choice()

    def get_choice(self):
        from resources.lib.kodiutils import isactive_winprop
        with isactive_winprop('SkinViewtypes.DialogIsActive'):
            return self.select()

    def select(self):
        current = self
        while current.items:
            params = {'useDetails': bool(current.viewtypes_obj.icons), 'preselect': current.preselect}
            params = {key: value for key, value in params.items() if value is not None}
            index = Dialog().select(current.header, [item.item for item in current.items], **params)
            if index != -1:
                return current.items[index]
            if not current.viewtypes_obj.groups:
                return
            current = ViewTypesPluginView(self.viewtypes_obj, self.contentid, self.pluginname)

    @cached_property
    def view_id(self):
        return self.get_view_id()

    def get_view_id(self):
        if not self.contentid or not self.pluginname or not self.content or not self.choice:
            return
        return self.choice.view_id
