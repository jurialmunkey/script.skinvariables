# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import ListItem
from infotagger.listitem import ListItemInfoTag
from jurialmunkey.litems import INFOLABEL_MAP


DIRECTORY_PROPERTIES_BASIC = ["title", "art", "file", "fanart"]

DIRECTORY_PROPERTIES_VIDEO = [
    'genre',
    'year',
    'rating',
    'playcount',
    'director',
    'trailer',
    'tagline',
    'plot',
    'plotoutline',
    'originaltitle',
    'lastplayed',
    'writer',
    'studio',
    'mpaa',
    'country',
    'premiered',
    'runtime',
    'set',
    'streamdetails',
    'top250',
    'votes',
    'firstaired',
    'season',
    'episode',
    'showtitle',
    'tvshowid',
    'setid',
    'sorttitle',
    'thumbnail',
    'uniqueid',
    'dateadded',
    'resume',
    'customproperties',
]

DIRECTORY_PROPERTIES_MUSIC = [
    'artist',
    'albumartist',
    'genre',
    'year',
    'rating',
    'album',
    'track',
    'duration',
    'lastplayed',
    'studio',
    'mpaa',
    'disc',
    'description',
    'theme',
    'mood',
    'style',
    'albumlabel',
    'sorttitle',
    'uniqueid',
    'dateadded',
    'customproperties',
    'totaldiscs',
    'disctitle',
    'releasedate',
    'originaldate',
    'bpm',
    'bitrate',
    'samplerate',
    'channels',
]

INFOPROPERTY_MAP = {
    "disctitle": "disctitle",
    "releasedate": "releasedate",
    "originaldate": "originaldate",
    "bpm": "bpm",
    "bitrate": "bitrate",
    "samplerate": "samplerate",
    "channels": "channels",
    "totaldiscs": "totaldiscs",
    "disc": "disc",
    "description": "description",
    "theme": "theme",
    "mood": "mood",
    "style": "style",
    "albumlabel": "albumlabel",
    "tvshowid": "tvshow.dbid",
    "setid": "set.dbid",
    "songvideourl": "songvideourl",
}


def get_directory_properties(library):
    properties = DIRECTORY_PROPERTIES_BASIC + {
        'video': DIRECTORY_PROPERTIES_VIDEO,
        'music': DIRECTORY_PROPERTIES_MUSIC,
    }.get(library, [])
    if library != 'music':
        return properties
    from jurialmunkey.jsnrpc import get_jsonrpc
    version = get_jsonrpc('JSONRPC.Version')['result']['version']
    version = tuple(version[key] for key in ('major', 'minor', 'patch'))
    if version >= (13, 3, 0):
        properties.append('songvideourl')
    return properties


class MetaItemJSONRPC:
    def __init__(self, meta, dbtype='video'):
        self.meta = meta or {}
        self.dbtype = dbtype

    @property
    def title(self):
        return self.meta.get('title') or self.meta.get('label') or ''

    @property
    def label(self):
        return self.get_label()

    def get_label(self):
        if self.path.startswith('plugin://') and self.meta.get('label'):  # Prefer label for plugin items
            return self.meta['label']
        return self.title

    @property
    def path(self):
        return self.meta.get('file') or ''

    @property
    def mediatype(self):
        return self.get_mediatype()

    def get_mediatype(self):
        mediatype = self.meta.get('type') or ''
        if mediatype in ('unknown', ''):
            return self.dbtype
        return mediatype

    @property
    def infolabels(self):
        return self.get_infolabels()

    def get_infolabels(self):
        return {INFOLABEL_MAP[k]: v for k, v in self.meta.items() if v and k in INFOLABEL_MAP and v != -1}

    @property
    def infoproperties(self):
        return self.get_infoproperties()

    def get_infoproperties(self):
        infoproperties = {
            INFOPROPERTY_MAP[key]: str(value)
            for key, value in self.meta.items()
            if value and key in INFOPROPERTY_MAP and value != -1
        }
        infoproperties.update({k: str(v) for k, v in (self.meta.get('customproperties') or {}).items()})
        infoproperties.update(self.resume)
        return infoproperties

    @property
    def resume(self):
        return self.get_resume()

    def get_resume(self):
        resume = self.meta.get('resume') or {}
        infoproperties = {}
        if resume.get('total'):
            infoproperties['resumetime'] = resume.get('position') or 0
            infoproperties['totaltime'] = resume.get('total')
            infoproperties['percentplayed'] = int(infoproperties['resumetime'] / infoproperties['totaltime'] * 100)
        return infoproperties

    @property
    def uniqueids(self):
        return self.meta.get('uniqueid') or {}

    @property
    def streamdetails(self):
        return self.meta.get('streamdetails') or {}

    @property
    def artwork(self):
        return self.get_artwork()

    def get_artwork(self):
        artwork = dict(self.meta.get('art') or {})
        for key in ('thumb', 'fanart'):
            if self.meta.get(key) and not artwork.get(key):
                artwork[key] = self.meta[key]
        return artwork

    @property
    def filetype(self):
        return self.meta.get('filetype')


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
    def mediatype(self):
        return self._mediatype

    @mediatype.setter
    def mediatype(self, value: str):
        self._mediatype = value
        self.infolabels['mediatype'] = value

    @property
    def infolabels(self):
        return self._infolabels

    @infolabels.setter
    def infolabels(self, value):
        self._infolabels = value
        self.fix_music_infolabels()

    def fix_music_infolabels(self):
        # Fix some incompatible type returns from JSON RPC to info_tag in music library
        if self.library != 'music':
            return
        for a in ('artist', 'albumartist', 'album'):
            if not isinstance(self.infolabels.get(a), list):
                continue
            self.infolabels[a] = ' / '.join(self.infolabels[a])

    @property
    def artwork(self):
        return self._artwork

    @artwork.setter
    def artwork(self, value):
        self._artwork = value
        if self.library == 'music':
            for key in ('thumb', 'fanart', 'clearlogo'):
                self._artwork[key] = self.get_music_artwork(key)

    def get_music_artwork(self, key):
        names = (key,) + tuple(f'{parent}.{key}' for parent in ('album', 'albumartist', 'artist'))
        for name in names:
            if self.artwork.get(name):
                return self.artwork[name]
        return ''

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value
        self.is_folder = True

        if self.filetype == 'file':
            self.is_folder = False
            self.infoproperties['isPlayable'] = 'true'
            return

        if '://' in self._path:
            return

        if self.mediatype == 'tvshow' and self.infolabels.get('dbid'):
            self._path = f'videodb://tvshows/titles/{self.infolabels["dbid"]}/'
            return

        if self.mediatype == 'season' and self.infolabels.get('tvshow.dbid'):
            self._path = f'videodb://tvshows/titles/{self.infoproperties["tvshow.dbid"]}/{self.infolabels["season"]}/'
            return

    @property
    def listitem(self):
        return self.get_listitem()

    def get_listitem(self):
        self._listitem = ListItem(label=self.label, label2=self.label2, path=self.path, offscreen=True)
        self._listitem.setLabel2(self.label2)
        self._listitem.setArt(self.artwork)

        self._info_tag = ListItemInfoTag(self._listitem, self.library)
        self._info_tag.set_info(self.infolabels)
        if self.library == 'video':
            self._info_tag.set_unique_ids(self.uniqueids)
            self._info_tag.set_stream_details(self.streamdetails)
            self._info_tag.set_resume_point(self.infoproperties, resume_key='resumetime', total_key='totaltime')

        self._listitem.setProperties(self.infoproperties)
        return self._listitem
