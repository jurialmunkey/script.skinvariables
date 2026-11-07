# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from jurialmunkey.jsnrpc import get_jsonrpc
from jurialmunkey.litems import ContainerDirectory


class PlayerStreamItem:
    def __init__(self, meta, stream_type, current_index):
        self.meta = meta
        self.stream_type = stream_type
        self.current_index = current_index

    @property
    def label(self):
        return self.meta.get('language', 'UND')

    @property
    def label2(self):
        return self.meta.get('name', '')

    @property
    def index(self):
        return self.meta.get('index')

    @cached_property
    def path(self):
        return self.get_path()

    def get_path(self):
        basepath = 'plugin://script.skinvariables/?info=set_player_streams'
        return f'{basepath}&stream_index={self.index}&stream_type={self.stream_type}'

    @cached_property
    def properties(self):
        return self.get_properties()

    def get_properties(self):
        properties = {f'{key}': f'{value}' for key, value in self.meta.items() if value}
        if self.current_index == self.index:
            properties['iscurrent'] = 'true'
        properties['isfolder'] = 'false'
        return properties

    @cached_property
    def item(self):
        return self.get_item()

    def get_item(self):
        item = ContainerDirectory.get_list_item(self.label, self.label2, self.path, is_folder=False)
        item[1].setProperties(self.properties)
        return (item[1].getPath(), item[1], item[1].getProperty('isfolder').lower() == 'true')


class PlayerStreams:
    """Load and cache one stream type for a single directory request."""

    stream_type = None
    stream_key = None
    current_key = None

    @cached_property
    def params(self):
        return self.get_params()

    def get_params(self):
        return {'playerid': 1, 'properties': [self.stream_key, self.current_key]}

    @cached_property
    def metadata(self):
        return self.get_metadata()

    def get_metadata(self):
        response = get_jsonrpc('Player.GetProperties', self.params) or {}
        return response.get('result', {})

    @cached_property
    def streams(self):
        return self.get_streams()

    def get_streams(self):
        return self.metadata.get(self.stream_key) or []

    @cached_property
    def current_index(self):
        return self.get_current_index()

    def get_current_index(self):
        return self.metadata.get(self.current_key, {}).get('index', 0)

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        if not self.streams:
            return []
        current_index = self.current_index
        return [PlayerStreamItem(meta, self.stream_type, current_index).item for meta in self.streams if meta]


class AudioPlayerStreams(PlayerStreams):
    stream_type = 'audio'
    stream_key = 'audiostreams'
    current_key = 'currentaudiostream'


class SubtitlePlayerStreams(PlayerStreams):
    stream_type = 'subtitle'
    stream_key = 'subtitles'
    current_key = 'currentsubtitle'


PLAYER_STREAM_CLASSES = {'audio': AudioPlayerStreams, 'subtitle': SubtitlePlayerStreams}
