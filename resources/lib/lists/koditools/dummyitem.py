# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from infotagger.listitem import ListItemInfoTag
from jurialmunkey.ftools import cached_property
from jurialmunkey.litems import ContainerDirectory


STREAM_DETAIL_CONVERSIONS = {
    'video': {
        'width': int,
        'height': int,
        'aspect': float,
        'duration': int,
        'codec': str,
        'stereomode': str,
        'language': str,
        'hdrtype': str,
    },
    'audio': {
        'channels': int,
        'codec': str,
        'language': str,
    },
}


class DummyItem:
    """
    One video list item built from plugin params, so skins can preview real infolabels without a library item.
    Plain params are video infolabels, for example mediatype, title, duration (seconds), rating, premiered, year and mpaa.
    Params named video.<key> or audio.<key> add one stream of that type, for example video.width, video.hdrtype and audio.channels.
    """

    def __init__(self, label='', **params):
        self.label = label
        self.params = params

    @cached_property
    def infolabels(self):
        return self.get_infolabels()

    def get_infolabels(self):
        return {key: value for key, value in self.params.items() if '.' not in key}

    def get_stream(self, stream_type):
        conversions = STREAM_DETAIL_CONVERSIONS[stream_type]
        values = {
            key.partition('.')[2]: value
            for key, value in self.params.items()
            if key.partition('.')[0] == stream_type
        }
        return {key: conversions[key](value) for key, value in values.items()}

    @cached_property
    def stream_details(self):
        return self.get_stream_details()

    def get_stream_details(self):
        streams = {stream_type: self.get_stream(stream_type) for stream_type in STREAM_DETAIL_CONVERSIONS}
        return {stream_type: [stream] for stream_type, stream in streams.items() if stream}

    @cached_property
    def item(self):
        return self.get_item()

    def get_item(self):
        path, listitem, is_folder = ContainerDirectory.get_list_item(self.label, is_folder=False)
        info_tag = ListItemInfoTag(listitem, 'video')
        info_tag.set_info(self.infolabels)
        info_tag.set_stream_details(self.stream_details)
        return (path, listitem, is_folder)


class ListGetDummyItem(ContainerDirectory):
    def get_directory(self, info=None, **kwargs):
        self.add_items([DummyItem(**kwargs).item])
