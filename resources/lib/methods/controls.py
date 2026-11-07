# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import xbmcgui
from jurialmunkey.jsnrpc import get_jsonrpc


def set_animation_list(animations):
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    for control_id, event, effect in animations:
        window.getControl(int(control_id)).setAnimations([(event, effect)])


def set_animation(set_animation, **kwargs):
    set_animation_list([
        (control_id, event, effect)
        for item in set_animation.split('||')
        for control_id, event, effect in item.split('|')
    ])


def set_slider(window_id, control_id, value):
    window = xbmcgui.Window(int(window_id))
    window.getControl(int(control_id)).setPercent(int(value))


def set_editcontrol(set_editcontrol, text=None, window_id=None, setfocus=None, setfocus_wait='00:00', **kwargs):
    xbmc.executebuiltin(f'SetFocus({set_editcontrol})')
    get_jsonrpc('Input.SendText', {'text': text or '', 'done': True})
    if setfocus:
        xbmc.executebuiltin(f'AlarmClock(Refocus,SetFocus({setfocus}),{setfocus_wait},silent)')
