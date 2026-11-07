# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import time
import xbmc
from jurialmunkey.ftools import cached_property
from jurialmunkey.jsnrpc import get_jsonrpc
from jurialmunkey.parser import try_int


class PlayerStreamSetter:
    method = None
    stream_key = None

    def __init__(self, index, reload_property='UID'):
        self.index = index
        self.reload_property = reload_property

    @cached_property
    def params(self):
        return self.get_params()

    def get_params(self):
        return {'playerid': 1, self.stream_key: try_int(self.index)}

    def run(self):
        get_jsonrpc(self.method, self.params)
        xbmc.executebuiltin(f'SetProperty({self.reload_property},{time.time()})')


class AudioStreamSetter(PlayerStreamSetter):
    method = 'Player.SetAudioStream'
    stream_key = 'stream'


class SubtitleSetter(PlayerStreamSetter):
    method = 'Player.SetSubtitle'
    stream_key = 'subtitle'

    def get_params(self):
        return dict(super().get_params(), enable=True)


def set_player_subtitle(set_player_subtitle, reload_property='UID', **kwargs):
    SubtitleSetter(set_player_subtitle, reload_property).run()


def set_player_audiostream(set_player_audiostream, reload_property='UID', **kwargs):
    AudioStreamSetter(set_player_audiostream, reload_property).run()
