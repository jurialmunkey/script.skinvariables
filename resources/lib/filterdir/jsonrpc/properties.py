# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from jurialmunkey.jsnrpc import get_jsonrpc


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


class DirectoryProperties:
    extra_properties = ()

    @cached_property
    def properties(self):
        return self.get_properties()

    def get_properties(self):
        return DIRECTORY_PROPERTIES_BASIC + list(self.extra_properties)


class VideoDirectoryProperties(DirectoryProperties):
    extra_properties = DIRECTORY_PROPERTIES_VIDEO


class MusicDirectoryProperties(DirectoryProperties):
    extra_properties = DIRECTORY_PROPERTIES_MUSIC

    @cached_property
    def version(self):
        return self.get_version()

    def get_version(self):
        version = get_jsonrpc('JSONRPC.Version')['result']['version']
        return tuple(version[key] for key in ('major', 'minor', 'patch'))

    def get_properties(self):
        properties = super().get_properties()
        if self.version >= (13, 3, 0):
            properties.append('songvideourl')
        return properties


PROPERTY_CLASSES = {'video': VideoDirectoryProperties, 'music': MusicDirectoryProperties}


def get_directory_properties(library):
    return PROPERTY_CLASSES.get(library, DirectoryProperties)().properties
