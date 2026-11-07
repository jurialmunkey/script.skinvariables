# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property


class JSONRPCItemPath:
    def __init__(self, source, filetype, mediatype, infolabels, infoproperties):
        self.source = source
        self.filetype = filetype
        self.mediatype = mediatype
        self.infolabels = infolabels
        self.infoproperties = infoproperties

    @cached_property
    def is_folder(self):
        return self.get_is_folder()

    def get_is_folder(self):
        return self.filetype != 'file'

    @cached_property
    def playback_properties(self):
        return self.get_playback_properties()

    def get_playback_properties(self):
        return {} if self.is_folder else {'isPlayable': 'true'}

    @cached_property
    def path(self):
        return self.get_path()

    def get_path(self):
        if not self.is_folder or '://' in self.source:
            return self.source
        if self.mediatype == 'tvshow' and self.infolabels.get('dbid'):
            return f'videodb://tvshows/titles/{self.infolabels["dbid"]}/'
        if self.mediatype == 'season' and self.infolabels.get('tvshow.dbid'):
            return f'videodb://tvshows/titles/{self.infoproperties["tvshow.dbid"]}/{self.infolabels["season"]}/'
        return self.source
