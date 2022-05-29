# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import json
import xbmc
import xbmcgui
from resources.lib.kodiutils import kodi_log


def get_jsonrpc(method=None, params=None):
    if not method:
        return {}
    query = {
        "jsonrpc": "2.0",
        "method": method,
        "id": 1}
    if params:
        query["params"] = params
    try:
        jrpc = xbmc.executeJSONRPC(json.dumps(query))
        response = json.loads(jrpc)
    except Exception as exc:
        kodi_log(u'SkinVariables - JSONRPC Error:\n{}'.format(exc), 1)
        response = {}
    return response


PLAYERSTREAMS = {
    'audio': {'key': 'audiostreams', 'cur': 'currentaudiostream'},
    'subtitle': {'key': 'subtitles', 'cur': 'currentsubtitle'}
}


def get_player_streams(stream_type):
    def make_item(i):
        label = i.get("language", "UND")
        label2 = i.get("name", "")
        path = f'plugin://script.skinquicktools/?info=set_player_streams&stream_index={i.get("index")}&stream_type={stream_type}'
        infoproperties = {f'{k}': f'{v}' for k, v in i.items() if v}
        if cur_strm == i.get('index'):
            infoproperties['iscurrent'] = 'true'
        infoproperties['isfolder'] = 'false'
        listitem = xbmcgui.ListItem(label=label, label2=label2, path=path, offscreen=True)
        listitem.setProperties(infoproperties)
        return listitem

    ps_def = PLAYERSTREAMS.get(stream_type)
    if not ps_def:
        return []

    method = "Player.GetProperties"
    params = {"playerid": 1, "properties": [ps_def['key'], ps_def['cur']]}
    response = get_jsonrpc(method, params) or {}
    response = response.get('result', {})
    all_strm = response.get(ps_def['key']) or []
    if not all_strm:
        return []

    cur_strm = response.get(ps_def['cur'], {}).get('index', 0)
    return [make_item(i) for i in all_strm if i]
