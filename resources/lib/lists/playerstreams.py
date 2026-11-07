# -*- coding: utf-8 -*-
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.litems import ContainerDirectory
from resources.lib.playerstreams import PLAYER_STREAM_CLASSES


class ListGetPlayerStreams(ContainerDirectory):
    def get_directory(self, stream_type=None, **kwargs):
        if not stream_type:
            return
        stream_class = PLAYER_STREAM_CLASSES.get(stream_type)
        items = stream_class().items if stream_class is not None else []
        self.add_items(items)


class ListSetPlayerStreams(ContainerDirectory):
    def get_directory(self, stream_type=None, stream_index=None, **kwargs):
        if not stream_type or stream_index is None:
            return
        if stream_type == 'audio':
            from resources.lib.methods.player import set_player_audiostream
            set_player_audiostream(stream_index)
            return
        if stream_type == 'subtitle':
            from resources.lib.methods.player import set_player_subtitle
            set_player_subtitle(stream_index)
            return
