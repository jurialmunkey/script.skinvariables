# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sys
import xbmcplugin
from xbmcgui import ListItem
from jurialmunkey.parser import parse_paramstring
from jurialmunkey.jsnrpc import get_jsonrpc
from resources.lib.method import set_player_subtitle, set_player_audiostream


PLAYERSTREAMS = {
    'audio': {'key': 'audiostreams', 'cur': 'currentaudiostream'},
    'subtitle': {'key': 'subtitles', 'cur': 'currentsubtitle'}
}


class Plugin(object):
    def __init__(self):
        self.handle = int(sys.argv[1])
        self.paramstring = sys.argv[2][1:]
        self.params = parse_paramstring(self.paramstring)
        self.routes = {
            'get_player_streams': self.get_player_streams,
            'set_player_streams': self.set_player_streams
        }

    def add_items(self, items, update_listing=False, plugin_category='', container_content=''):
        for i in items:
            xbmcplugin.addDirectoryItem(handle=self.handle, **i)
        xbmcplugin.setPluginCategory(self.handle, plugin_category)  # Container.PluginCategory
        xbmcplugin.setContent(self.handle, container_content)  # Container.Content
        xbmcplugin.endOfDirectory(self.handle, updateListing=update_listing)

    def set_player_streams(self, stream_type=None, stream_index=None, **kwargs):
        if not stream_type or stream_index is None:
            return
        if stream_type == 'audio':
            set_player_audiostream(stream_index)
            return
        if stream_type == 'subtitle':
            set_player_subtitle(stream_index)
            return

    def get_player_streams(self, stream_type=None, **kwargs):
        def _get_items(stream_type):
            def make_item(i):
                label = i.get("language", "UND")
                label2 = i.get("name", "")
                path = f'plugin://script.skinvariables/?info=set_player_streams&stream_index={i.get("index")}&stream_type={stream_type}'
                infoproperties = {f'{k}': f'{v}' for k, v in i.items() if v}
                if cur_strm == i.get('index'):
                    infoproperties['iscurrent'] = 'true'
                infoproperties['isfolder'] = 'false'
                listitem = ListItem(label=label, label2=label2, path=path, offscreen=True)
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

        if not stream_type:
            return

        items = [
            {'url': li.getPath(), 'listitem': li, 'isFolder': li.getProperty('isfolder').lower() == 'true'}
            for li in _get_items(stream_type) if li]

        self.add_items(items)

    def run(self):
        if not self.params:
            return
        if self.params.get('info') not in self.routes:
            return
        self.routes[self.params['info']](**self.params)
