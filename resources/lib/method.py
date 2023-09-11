# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import jurialmunkey.futils
ADDONDATA = 'special://profile/addon_data/script.skinvariables/'


class FileUtils(jurialmunkey.futils.FileUtils):
    addondata = ADDONDATA   # Override module addon_data with plugin addon_data


def set_player_subtitle(set_player_subtitle, reload_property='UID', **kwargs):
    import time
    import xbmc
    from jurialmunkey.jsnrpc import get_jsonrpc
    from jurialmunkey.parser import try_int
    method = "Player.SetSubtitle"
    params = {"playerid": 1, "subtitle": try_int(set_player_subtitle), "enable": True}
    get_jsonrpc(method, params)
    xbmc.executebuiltin(f'SetProperty({reload_property},{time.time()})')


def set_player_audiostream(set_player_audiostream, reload_property='UID', **kwargs):
    import time
    import xbmc
    from jurialmunkey.jsnrpc import get_jsonrpc
    from jurialmunkey.parser import try_int
    method = "Player.SetAudioStream"
    params = {"playerid": 1, "stream": try_int(set_player_audiostream)}
    get_jsonrpc(method, params)
    xbmc.executebuiltin(f'SetProperty({reload_property},{time.time()})')


def set_editcontrol(set_editcontrol, text=None, window_id=None, setfocus=None, setfocus_wait='00:00', **kwargs):
    import xbmc
    from jurialmunkey.jsnrpc import get_jsonrpc
    xbmc.executebuiltin(f'SetFocus({set_editcontrol})')
    get_jsonrpc("Input.SendText", {"text": text or '', "done": True})
    xbmc.executebuiltin(f'AlarmClock(Refocus,SetFocus({setfocus}),{setfocus_wait},silent)') if setfocus else None


def add_skinstring_history(add_skinstring_history, value, separator='|', use_window_prop=False, window_id='', toggle=False, **kwargs):
    import xbmc

    def _get_info_str() -> str:
        if not use_window_prop:
            return 'Skin.String({})'
        if window_id:
            return f'Window({window_id}).Property({{}})'
        return 'Window.Property({})'

    values = xbmc.getInfoLabel(_get_info_str().format(add_skinstring_history)) or ''
    values = values.split(separator)
    if not values:
        return
    try:
        values.remove(value)
        remove = True
    except ValueError:
        remove = False
    if not toggle or not remove:
        values.insert(0, value)

    def _get_exec_str() -> str:
        if not use_window_prop:
            return 'Skin.SetString({},{})'
        if window_id:
            return f'SetProperty({{}},{{}},{window_id})'
        return 'SetProperty({},{})'

    xbmc.executebuiltin(_get_exec_str().format(add_skinstring_history, values[0]))


def set_dbid_tag(set_dbid_tag, dbtype, dbid, **kwargs):
    from jurialmunkey.jsnrpc import set_tags
    set_tags(int(dbid), dbtype, [set_dbid_tag])


def get_jsonrpc(get_jsonrpc, textviewer=False, filewrite=True, **kwargs):
    from jurialmunkey.jsnrpc import get_jsonrpc as _get_jsonrpc
    result = _get_jsonrpc(get_jsonrpc, kwargs)

    if textviewer:
        from xbmcgui import Dialog
        Dialog().textviewer(f'GET {get_jsonrpc}', f'PARAMS\n{kwargs}\n\nRESULT\n{result}')

    if filewrite:
        filename = '_'.join([f'{k}-{v}' for k, v in kwargs.items()])
        filename = jurialmunkey.futils.validify_filename(f'{get_jsonrpc}_{filename}.json')
        FileUtils().dumps_to_file({'method': get_jsonrpc, 'params': kwargs, 'result': result}, 'log_request', filename)
