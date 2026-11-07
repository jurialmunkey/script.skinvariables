# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.viewtypes.common import ADDON, get_localized


class ConfiguredViews:
    def __init__(self, items, viewtypes, listprefix='', idprefix='', contentid=''):
        self.items = items
        self.viewtypes = viewtypes
        self.listprefix = listprefix
        self.idprefix = idprefix
        self.contentid = contentid

    def get_entry(self, contentid, viewid):
        name = get_localized(self.viewtypes.get(viewid))
        label = f'{self.listprefix}{contentid.capitalize()} ({name})'
        return label, (self.idprefix, contentid)

    @cached_property
    def entries(self):
        return self.get_entries()

    def get_entries(self):
        return [
            self.get_entry(contentid, viewid)
            for contentid, viewid in self.items
            if not self.contentid or self.contentid == contentid
        ]


class ConfigurationMenu:
    def __init__(self, viewtypes, contentid, pluginname):
        self.viewtypes = viewtypes
        self.contentid = contentid
        self.pluginname = pluginname

    def get_default_entries(self, location, label):
        if self.pluginname and self.pluginname != location:
            return []
        return self.viewtypes.dc_listcomp(
            sorted(self.viewtypes.addon_meta.get(location, {}).items()),
            listprefix=label,
            idprefix=location,
            contentid=self.contentid,
        )

    def get_plugin_entries(self, pluginname, rules):
        name = self.viewtypes.get_addondetails(addonid=pluginname, prop='name')
        entries = self.viewtypes.dc_listcomp(
            sorted(rules.items()),
            listprefix=f'{name} - ',
            idprefix=pluginname,
            contentid=self.contentid,
        )
        return entries + [(f'Reset all {name} views...', (pluginname, 'default'))]

    @cached_property
    def plugins(self):
        return self.get_plugins()

    def get_plugins(self):
        if self.pluginname == 'library':
            return []
        return [
            entry
            for pluginname, rules in self.viewtypes.addon_meta.items()
            if pluginname not in ('library', 'plugins')
            if not self.pluginname or self.pluginname in ('plugins', pluginname)
            for entry in self.get_plugin_entries(pluginname, rules)
        ]

    @cached_property
    def actions(self):
        return self.get_actions()

    def get_actions(self):
        if self.contentid:
            return []
        entries = []
        if not self.pluginname or self.pluginname == 'plugins':
            entries.append((ADDON.getLocalizedString(32011).format('plugin'), ('plugins', 'default')))
        if not self.pluginname or self.pluginname == 'library':
            entries.append((ADDON.getLocalizedString(32011).format('library'), ('library', 'default')))
        if self.pluginname != 'library':
            entries.append((ADDON.getLocalizedString(32012), (None, 'add_pluginview')))
        return entries

    @cached_property
    def entries(self):
        return self.get_entries()

    def get_entries(self):
        library = self.get_default_entries('library', 'Library - ')
        plugins = self.get_default_entries('plugins', 'Plugins - ')
        return library + plugins + self.plugins + self.actions
