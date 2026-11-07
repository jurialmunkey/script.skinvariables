# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from infotagger.listitem import ListItemInfoTag


class JSONRPCLibrary:
    def __init__(self, library):
        self.library = library

    def normalize_infolabels(self, infolabels):
        return infolabels

    def normalize_artwork(self, artwork):
        return artwork

    def get_info_tag(self, listitem):
        return ListItemInfoTag(listitem, self.library)

    def set_info(self, info_tag, item):
        info_tag.set_info(item.infolabels)


class VideoJSONRPCLibrary(JSONRPCLibrary):
    def set_info(self, info_tag, item):
        super().set_info(info_tag, item)
        info_tag.set_unique_ids(item.uniqueids)
        info_tag.set_stream_details(item.streamdetails)
        info_tag.set_resume_point(item.infoproperties, resume_key='resumetime', total_key='totaltime')


class MusicArtwork:
    def __init__(self, artwork):
        self.artwork = artwork

    def get_fallback(self, key):
        names = (key,) + tuple(f'{parent}.{key}' for parent in ('album', 'albumartist', 'artist'))
        return next((self.artwork[name] for name in names if self.artwork.get(name)), '')

    @property
    def result(self):
        return self.get_result()

    def get_result(self):
        for key in ('thumb', 'fanart', 'clearlogo'):
            self.artwork[key] = self.get_fallback(key)
        return self.artwork


class MusicJSONRPCLibrary(JSONRPCLibrary):
    def normalize_infolabels(self, infolabels):
        for key in ('artist', 'albumartist', 'album'):
            if isinstance(infolabels.get(key), list):
                infolabels[key] = ' / '.join(infolabels[key])
        return infolabels

    def normalize_artwork(self, artwork):
        return MusicArtwork(artwork).result


def get_library(library):
    if library == 'video':
        return VideoJSONRPCLibrary(library)
    if library == 'music':
        return MusicJSONRPCLibrary(library)
    return JSONRPCLibrary(library)
