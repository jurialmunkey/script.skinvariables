# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import jurialmunkey.futils
import jurialmunkey.parser
ADDONDATA = 'special://profile/addon_data/script.skinvariables/'


class FileUtils(jurialmunkey.futils.FileUtils):
    addondata = ADDONDATA   # Override module addon_data with plugin addon_data


boolean = jurialmunkey.parser.boolean


def set_animation(set_animation, **kwargs):
    import xbmcgui
    win_id = xbmcgui.getCurrentWindowId()
    window = xbmcgui.Window(win_id)

    for i in set_animation.split('||'):
        control_id, event, effect = i.split('|')
        control = window.getControl(int(control_id))
        control.setAnimations([(event, effect,)])


def run_animation(
        list_id, movement, item_w, item_h, delay_multiplier=0, time=400, easing='out', tween='cubic', mod_offset=0,
        window_prop=None, clear_prop=False, executebuiltin=None, **kwargs):
    import xbmc
    import xbmcgui

    win_id = xbmcgui.getCurrentWindowId()
    window = xbmcgui.Window(win_id)

    list_id = int(list_id)
    item_pos_id = list_id * 1000
    item_neg_id = item_pos_id + 100

    mod_offset = int(mod_offset)

    item_spacer = int(item_w)
    item_height = int(item_h)
    delay_multiplier = int(delay_multiplier)
    time = int(time)
    movement = int(movement)

    item_range = (movement * 2)
    item_range += 2  # if is_even else 1
    item_range += 3  # For overhang

    def _get_mod_spacer():
        mod_item_range = (movement * 2)
        mod_position = int(xbmc.getInfoLabel(f'Container({list_id}).Position'))

        if mod_position != 0:
            mod_position += mod_offset

        for x in range(movement + 1):
            if xbmc.getInfoLabel(f'Container({list_id}).ListItemNoWrap({mod_item_range - (x * 2)}).CurrentItem'):
                return (item_spacer * x) - (item_spacer * mod_position)

        return 0

    mod_spacer = _get_mod_spacer()

    effect_fstr = f'effect=slide easing={easing} tween={tween} reversible=false'
    effect_fstr += ' time={time} delay={delay} start={start} end={end}'

    def _set_animation(control_id, event_effect_tuples):
        control = window.getControl(int(control_id))
        control.setAnimations(event_effect_tuples)

    if mod_offset % 2 == 0:
        top_row = -item_height
        low_row = 0
    else:
        top_row = 0
        low_row = -item_height

    for x in range(item_range):
        start_y = 0

        # Positive Positions
        delay = delay_multiplier * x
        start_x = item_spacer * x
        start_x -= mod_spacer

        end_y = low_row
        end_x = item_spacer * (x // 2)
        if x % 2 == 0:
            end_y = top_row

        _set_animation(item_pos_id + x, [
            ('visible', effect_fstr.format(time=time, delay=delay, start=f'{start_x},{start_y}', end=f'{end_x},{end_y}'), ),
            ('hidden', effect_fstr.format(time=time, delay=0, end=f'{start_x},{start_y}', start=f'{end_x},{end_y}'), ),
        ])

        # Main Item has no negative equivalent
        if x == 0:
            continue

        # Negative Positions
        delay = delay_multiplier * (x - 1)
        start_x = -(item_spacer * x)
        start_x -= mod_spacer

        end_y = top_row
        end_x = -(item_spacer * (x // 2))
        if x % 2 != 0:
            end_y = low_row
            end_x -= item_spacer

        _set_animation(item_neg_id + x, [
            ('visible', effect_fstr.format(time=time, delay=delay, start=f'{start_x},{start_y}', end=f'{end_x},{end_y}'),),
            ('hidden', effect_fstr.format(time=time, delay=0, end=f'{start_x},{start_y}', start=f'{end_x},{end_y}'),),
        ])

    if window_prop:
        if mod_offset:
            xbmc.executebuiltin(f'Control.Move({list_id},{mod_offset})')
        if not boolean(clear_prop):
            xbmc.executebuiltin(f'SetProperty({window_prop}.{list_id}.Max,{item_range - 1})')
            xbmc.executebuiltin(f'SetProperty({window_prop},1)')
        else:
            xbmc.executebuiltin(f'ClearProperty({window_prop})')

    if not executebuiltin:
        return

    for builtin in executebuiltin.split('||'):
        if builtin.startswith('sleep='):
            xbmc.Monitor().waitForAbort(float(builtin[6:]))
            continue
        xbmc.executebuiltin(builtin)


def get_paramstring_tuplepairs(paramstring):
    if not paramstring:
        return []
    return [tuple(i.split(';')) for i in paramstring.split(';;')]


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


def run_dialog(run_dialog, separator=' / ', **kwargs):
    import xbmcgui

    def _split_items(items):
        return items.split(separator)

    def _get_path_or_str(string):
        if not boolean(kwargs.get('load_file')):
            return str(string)
        from jurialmunkey.futils import load_filecontent
        return str(load_filecontent(string))

    def _get_preselected_items(string):
        if not string:
            return -1
        try:
            return int(string)
        except TypeError:
            return -1
        except ValueError:
            pass
        items = _split_items(kwargs.get('list') or '')
        if not items:
            return -1
        if len(items) == 0:
            return -1
        if string not in items:
            return -1
        return items.index(string)

    dialog = xbmcgui.Dialog()

    dialog_standard_routes = {
        'ok': {
            'func': dialog.ok,
            'params': (
                ('heading', str, ''), ('message', _get_path_or_str, ''), )
        },
        'yesno': {
            'func': dialog.yesno,
            'params': (
                ('heading', str, ''), ('message', _get_path_or_str, ''), ('nolabel', str, 'No'), ('yeslabel', str, 'Yes'),
                ('defaultbutton', int, xbmcgui.DLG_YESNO_YES_BTN), ('autoclose', int, 0), )
        },
        'yesnocustom': {
            'func': dialog.yesnocustom,
            'params': (
                ('heading', str, ''), ('message', _get_path_or_str, ''), ('nolabel', str, 'No'), ('yeslabel', str, 'Yes'), ('customlabel', str, 'Custom'),
                ('defaultbutton', int, xbmcgui.DLG_YESNO_YES_BTN), ('autoclose', int, 0), )
        },
        'textviewer': {
            'func': dialog.textviewer,
            'params': (
                ('heading', str, ''), ('text', _get_path_or_str, ''),
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
                ('list', _split_items, ''), )
        },
        'select': {
            'func': dialog.select,
            'params': (
                ('heading', str, ''),
                ('list', _split_items, ''),
                ('autoclose', int, 0), ('preselect', _get_preselected_items, -1), ('useDetails', boolean, False), )
        },
        'multiselect': {
            'func': dialog.select,
            'params': (
                ('heading', str, ''),
                ('list', _split_items, ''),
                ('autoclose', int, 0), ('preselect', _get_preselected_items, -1), ('useDetails', boolean, False), )
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
