# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import Dialog
from abc import ABC, abstractmethod
from resources.lib.viewtypes.common import ADDON
from resources.lib.viewtypes.menu import ConfigurationMenu


class ResetViews(ABC):
    def __init__(self, viewtypes, pluginname):
        self.viewtypes = viewtypes
        self.pluginname = pluginname

    @abstractmethod
    def reset(self):
        pass

    def run(self):
        choice = Dialog().yesno(
            ADDON.getLocalizedString(32014).format(self.pluginname),
            ADDON.getLocalizedString(32015).format(self.pluginname),
        )
        if choice:
            self.reset()
        return choice


class ResetAddonViews(ResetViews):
    def reset(self):
        if self.pluginname:
            self.viewtypes.addon_meta.pop(self.pluginname)


class ResetDefaultViews(ResetViews):
    def reset(self):
        self.viewtypes.addon_meta[self.pluginname] = self.viewtypes.addon_meta_defaultjson.get(self.pluginname, {})


class ResetPluginViews(ResetDefaultViews):
    def reset(self):
        super().reset()
        for pluginname in self.viewtypes.addon_meta.copy():
            if pluginname not in ('library', 'plugins'):
                self.viewtypes.addon_meta.pop(pluginname)


class ViewTypesConfiguration:
    def __init__(self, viewtypes, contentid, pluginname):
        self.viewtypes = viewtypes
        self.contentid = contentid
        self.pluginname = pluginname

    def reset(self, pluginname):
        reset_classes = {'library': ResetDefaultViews, 'plugins': ResetPluginViews}
        reset_class = reset_classes.get(pluginname, ResetAddonViews)
        return reset_class(self.viewtypes, pluginname).run()

    def apply(self, pluginname, contentid):
        if contentid == 'default':
            return self.reset(pluginname)
        if contentid == 'add_pluginview':
            return self.viewtypes.add_newplugin()
        return self.viewtypes.add_pluginview(contentid=contentid.lower(), pluginname=pluginname.lower())

    def run(self, force=False):
        while True:
            entries = ConfigurationMenu(self.viewtypes, self.contentid, self.pluginname).entries
            index = Dialog().select(ADDON.getLocalizedString(32013), [entry[0] for entry in entries])
            if index == -1:
                return force
            choice = self.apply(*entries[index][1])
            force = force or choice
