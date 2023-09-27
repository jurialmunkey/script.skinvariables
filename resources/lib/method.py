# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import jurialmunkey.futils
ADDONDATA = 'special://profile/addon_data/script.skinvariables/'


class FileUtils(jurialmunkey.futils.FileUtils):
    addondata = ADDONDATA   # Override module addon_data with plugin addon_data


def boolean(string):
    if not isinstance(string, str):
        return bool(string)
    if string.lower() in ('false', '0', ''):
        return False
    return True


def executebuiltin(executebuiltin='', index=None, values=None, **kwargs):
    if index == -1 or index is False:
        return

    if isinstance(index, int):
        executebuiltin = kwargs.get(f'executebuiltin_{index}') or executebuiltin
        value = values[index] if values else index
    else:
        value = index

    if not executebuiltin:
        return

    import xbmc
    for builtin in executebuiltin.split('||'):
        xbmc.executebuiltin(builtin.format(x=index, v=value))


def run_progressdialog(run_progressdialog, background=False, heading='', message='', polling='0.1', message_info='', progress_info='', timeout='200', max_value='100', **kwargs):
    import xbmc
    import xbmcgui

    func = xbmcgui.DialogProgressBG if boolean(background) else xbmcgui.DialogProgress
    dialog = func()

    polling = float(polling)
    timeout = int(timeout)
    max_value = int(max_value)

    monitor = xbmc.Monitor()
    dialog.create(heading, message)

    x = 0
    while x < max_value and timeout > 0 and not monitor.abortRequested():
        x += 1
        timeout -= 1
        if progress_info:
            x = int(xbmc.getInfoLabel(progress_info) or 0)
        if message_info:
            message = str(xbmc.getInfoLabel(message_info) or '')
        progress = int((x / max_value) * 100)
        dialog.update(progress, message=message)
        monitor.waitForAbort(polling)
    dialog.close()
    del dialog
    del monitor


def run_dialog(run_dialog, **kwargs):
    import xbmcgui
    from jurialmunkey.parser import split_items

    dialog = xbmcgui.Dialog()

    dialog_standard_routes = {
        'ok': {
            'func': dialog.ok,
            'params': (
                ('heading', str, ''), ('message', str, ''), )
        },
        'yesno': {
            'func': dialog.yesno,
            'params': (
                ('heading', str, ''), ('message', str, ''), ('nolabel', str, 'No'), ('yeslabel', str, 'Yes'),
                ('defaultbutton', int, xbmcgui.DLG_YESNO_YES_BTN), ('autoclose', int, 0), )
        },
        'yesnocustom': {
            'func': dialog.yesnocustom,
            'params': (
                ('heading', str, ''), ('message', str, ''), ('nolabel', str, 'No'), ('yeslabel', str, 'Yes'), ('customlabel', str, 'Custom'),
                ('defaultbutton', int, xbmcgui.DLG_YESNO_YES_BTN), ('autoclose', int, 0), )
        },
        'textviewer': {
            'func': dialog.textviewer,
            'params': (
                ('heading', str, ''), ('text', str, ''),
                ('usemono', boolean, True), )
        },
        'notification': {
            'func': dialog.notification,
            'params': (
                ('heading', str, ''), ('message', str, ''), ('icon', str, ''),
                ('time', int, 5000), ('sound', boolean, True), )
        },
        'numeric': {
            'func': dialog.numeric,
            'params': (
                ('heading', str, ''), ('defaultt', str, ''),
                ('type', int, 0), ('bHiddenInput', boolean, False), )
        },
        'input': {
            'func': dialog.input,
            'params': (
                ('heading', str, ''), ('defaultt', str, ''),
                ('type', int, xbmcgui.INPUT_ALPHANUM), ('option', int, 0), ('autoclose', int, 0), )
        },
        'browse': {
            'func': dialog.browse,
            'params': (
                ('heading', str, ''), ('shares', str, ''), ('mask', str, ''), ('defaultt', str, ''),
                ('type', int, 0), ('useThumbs', boolean, True), ('treatAsFolder', boolean, True), ('enableMultiple', boolean, True), )
        },
        'colorpicker': {
            'func': dialog.colorpicker,
            'params': (
                ('heading', str, ''), ('selectedcolor', str, ''), ('colorfile', str, ''), )
        },
        'contextmenu': {
            'func': dialog.contextmenu,
            'params': (
                ('list', split_items, ''), )
        },
        'select': {
            'func': dialog.select,
            'params': (
                ('heading', str, ''),
                ('list', split_items, ''),
                ('autoclose', int, 0), ('preselect', int, 0), ('useDetails', boolean, False), )
        },
        'multiselect': {
            'func': dialog.select,
            'params': (
                ('heading', str, ''),
                ('list', split_items, ''),
                ('autoclose', int, 0), ('preselect', int, 0), ('useDetails', boolean, False), )
        },
    }

    route = dialog_standard_routes[run_dialog]
    params = {k: func(kwargs.get(k) or fallback) for k, func, fallback in route['params']}
    executebuiltin(index=route['func'](**params), values=params.get('list'), **kwargs)


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

    xbmc.executebuiltin(_get_exec_str().format(add_skinstring_history, separator.join(filter(None, values))))


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
