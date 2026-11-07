# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from jurialmunkey.litems import INFOLABEL_MAP


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


class ResumeProperties:
    def __init__(self, resume):
        self.resume = resume

    @cached_property
    def total(self):
        return self.get_total()

    def get_total(self):
        return self.resume.get('total')

    @cached_property
    def position(self):
        return self.get_position()

    def get_position(self):
        return self.resume.get('position') or 0

    @cached_property
    def percent(self):
        return self.get_percent()

    def get_percent(self):
        return int(self.position / self.total * 100)

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        if not self.total:
            return {}
        return {'resumetime': self.position, 'totaltime': self.total, 'percentplayed': self.percent}


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
        return {
            INFOLABEL_MAP[key]: value
            for key, value in self.meta.items()
            if value and key in INFOLABEL_MAP and value != -1
        }

    @property
    def infoproperties(self):
        return self.get_infoproperties()

    def get_infoproperties(self):
        infoproperties = {
            INFOPROPERTY_MAP[key]: str(value)
            for key, value in self.meta.items()
            if value and key in INFOPROPERTY_MAP and value != -1
        }
        infoproperties.update({key: str(value) for key, value in (self.meta.get('customproperties') or {}).items()})
        infoproperties.update(self.resume)
        return infoproperties

    @property
    def resume(self):
        return self.get_resume()

    def get_resume(self):
        return ResumeProperties(self.meta.get('resume') or {}).result

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
