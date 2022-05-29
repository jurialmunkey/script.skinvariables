# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import time
import xbmcgui
from resources.lib.jsonrpc import get_jsonrpc
from resources.lib.kodiutils import try_int


def set_player_subtitle(set_player_subtitle, reload_property='UID', **kwargs):
    method = "Player.SetSubtitle"
    params = {"playerid": 1, "subtitle": try_int(set_player_subtitle), "enable": True}
    get_jsonrpc(method, params)
    xbmc.executebuiltin(f'SetProperty({reload_property},{time.time()})')


def set_player_audiostream(set_player_audiostream, reload_property='UID', **kwargs):
    method = "Player.SetAudioStream"
    params = {"playerid": 1, "stream": try_int(set_player_audiostream)}
    get_jsonrpc(method, params)
    xbmc.executebuiltin(f'SetProperty({reload_property},{time.time()})')


def set_editcontrol(set_editcontrol, text, window_id=None, setfocus=None, setfocus_wait='00:00', **kwargs):
    window_id = int(window_id or xbmcgui.getCurrentWindowId())
    window_id += 10000 if window_id < 10000 else 0
    my_window = xbmcgui.Window(window_id)
    my_window.getControl(int(set_editcontrol)).setText(text)
    xbmc.executebuiltin(f'AlarmClock(Refocus,SetFocus({setfocus}),{setfocus_wait},silent)') if setfocus else None
