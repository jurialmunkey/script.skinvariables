# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.shortcuts.artwork import DirectoryArtwork



class GetDirectoryCommon:
    def __init__(self, path, library='video', dbtype='video', definitions=None, target=None):
        self.path = path
        self.library = library
        self.dbtype = dbtype
        self.target = target
        self.definitions = definitions or {}

    @cached_property
    def directory(self):
        return self.get_directory()

    @cached_property
    def items(self):
        return self.get_items()

    def get_artwork_fallback(self, listitem):
        return DirectoryArtwork(listitem.artwork, self.definitions).result
