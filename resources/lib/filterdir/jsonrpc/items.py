# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import ListItem
from resources.lib.filterdir.jsonrpc.libraries import get_library
from resources.lib.filterdir.jsonrpc.metadata import MetaItemJSONRPC
from resources.lib.filterdir.jsonrpc.paths import JSONRPCItemPath


class ListItemJSONRPC:
    def __init__(self, meta, library='video', dbtype='video'):
        self.meta = MetaItemJSONRPC(meta, dbtype)
        self.is_folder = True
        self.library = library or 'video'
        self.infolabels = self.meta.infolabels
        self.infoproperties = self.meta.infoproperties
        self.uniqueids = self.meta.uniqueids
        self.streamdetails = self.meta.streamdetails
        self.artwork = self.meta.artwork
        self.filetype = self.meta.filetype
        self.mediatype = self.meta.mediatype
        self.path = self.meta.path
        self.label = self.meta.label
        self.label2 = ''

    @property
    def library_adapter(self):
        return self.get_library_adapter()

    def get_library_adapter(self):
        return get_library(self.library)

    @property
    def mediatype(self):
        return self._mediatype

    @mediatype.setter
    def mediatype(self, value):
        self._mediatype = value
        self.infolabels['mediatype'] = value

    @property
    def infolabels(self):
        return self._infolabels

    @infolabels.setter
    def infolabels(self, value):
        self._infolabels = value
        self.library_adapter.normalize_infolabels(value)

    @property
    def artwork(self):
        return self._artwork

    @artwork.setter
    def artwork(self, value):
        self._artwork = value
        self.library_adapter.normalize_artwork(value)

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value
        resolved = JSONRPCItemPath(value, self.filetype, self.mediatype, self.infolabels, self.infoproperties)
        self.is_folder = resolved.is_folder
        for key, property_value in resolved.playback_properties.items():
            self.infoproperties[key] = property_value
        self._path = resolved.path

    @property
    def listitem(self):
        return self.get_listitem()

    def get_listitem(self):
        self._listitem = ListItem(label=self.label, label2=self.label2, path=self.path, offscreen=True)
        self._listitem.setLabel2(self.label2)
        self._listitem.setArt(self.artwork)
        library = self.library_adapter
        self._info_tag = library.get_info_tag(self._listitem)
        library.set_info(self._info_tag, self)
        self._listitem.setProperties(self.infoproperties)
        return self._listitem
