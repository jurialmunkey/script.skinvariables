# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import Dialog, ListItem
from jurialmunkey.ftools import cached_property
from jurialmunkey.jsnrpc import get_jsonrpc
from resources.lib.viewtypes.common import ADDON


class AddonCatalog:
    def get_addons(self, addon_type):
        params = {'type': addon_type, 'properties': ['name', 'thumbnail']}
        return get_jsonrpc('Addons.GetAddons', params).get('result', {}).get('addons') or []

    @cached_property
    def addons(self):
        return self.get_catalog()

    def get_catalog(self):
        video = self.get_addons('xbmc.addon.video')
        audio = self.get_addons('xbmc.addon.audio')
        image = self.get_addons('xbmc.addon.image')
        return video + audio + image

    def get_item(self, addon):
        item = ListItem(label=addon.get('name'), label2=str(addon.get('addonid')))
        item.setArt({'icon': addon.get('thumbnail'), 'thumb': addon.get('thumbnail')})
        return item

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        return [self.get_item(addon) for addon in self.addons]

    @cached_property
    def ids(self):
        return self.get_ids()

    def get_ids(self):
        return [addon.get('addonid') for addon in self.addons]


class AddonDetails:
    def __init__(self, addonid, prop):
        self.addonid = addonid
        self.prop = prop

    @cached_property
    def value(self):
        return self.get_value()

    def get_value(self):
        if not self.addonid or not self.prop:
            return
        params = {'addonid': self.addonid, 'properties': [self.prop]}
        return get_jsonrpc('Addons.GetAddonDetails', params).get('result', {}).get('addon', {}).get(self.prop)


class NewPluginDialog:
    def __init__(self, viewtypes):
        self.viewtypes = viewtypes

    def run(self):
        while True:
            catalog = AddonCatalog()
            index = Dialog().select(ADDON.getLocalizedString(32009), catalog.items, useDetails=True)
            if index == -1:
                return
            pluginname = catalog.ids[index]
            contentids = sorted(self.viewtypes.meta.get('rules', {}))
            index = Dialog().select(ADDON.getLocalizedString(32010), contentids)
            if index != -1:
                return self.viewtypes.add_pluginview(pluginname=pluginname, contentid=contentids[index])
