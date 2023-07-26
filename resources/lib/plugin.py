# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import ListItem


PLAYERSTREAMS = {
    'audio': {'key': 'audiostreams', 'cur': 'currentaudiostream'},
    'subtitle': {'key': 'subtitles', 'cur': 'currentsubtitle'}
}


class Container():
    def __init__(self, handle, paramstring, **params):
        self.handle = handle
        self.paramstring = paramstring
        self.params = params

    def add_items(self, items, update_listing=False, plugin_category='', container_content=''):
        import xbmcplugin
        for i in items:
            xbmcplugin.addDirectoryItem(handle=self.handle, **i)
        xbmcplugin.setPluginCategory(self.handle, plugin_category)  # Container.PluginCategory
        xbmcplugin.setContent(self.handle, container_content)  # Container.Content
        xbmcplugin.endOfDirectory(self.handle, updateListing=update_listing)


class ListGetItemDetails(Container):
    jrpc_method = ""
    jrpc_properties = []
    jrpc_id = ""
    jrpc_key = ""

    @staticmethod
    def make_item(i):
        label = i.get('label') or ''
        label2 = ''
        path = f'plugin://script.skinvariables/'

        artwork = i.pop('art', {})
        artwork.setdefault('fanart', i.pop('fanart', ''))
        artwork.setdefault('thumb', i.pop('thumbnail', ''))

        def _iter_dict(d, prefix=''):
            ip = {}
            for k, v in d.items():
                if isinstance(v, dict):
                    ip.update(_iter_dict(v, prefix=f'{prefix}{k}.'))
                    continue
                if isinstance(v, list):
                    for x, j in enumerate(v):
                        if isinstance(j, dict):
                            ip.update(_iter_dict(j, prefix=f'{prefix}{k}.{x}.'))
                            continue
                        ip[f'{prefix}{k}.{x}'] = f'{j}'
                    continue
                ip[f'{prefix}{k}'] = f'{v}'
            return ip

        infoproperties = {}
        infoproperties.update(_iter_dict(i))
        infoproperties['isfolder'] = 'false'
        # from resources.lib.kodiutils import kodi_log
        # kodi_log(f'ip {infoproperties}', 1)

        listitem = ListItem(label=label, label2=label2, path=path, offscreen=True)
        listitem.setProperties(infoproperties)
        listitem.setArt(artwork)

        return listitem

    def get_directory(self, dbid, **kwargs):
        from jurialmunkey.jsnrpc import get_jsonrpc

        def _get_items():
            method = self.jrpc_method
            params = {
                self.jrpc_id: int(dbid),
                "properties": self.jrpc_properties
            }
            response = get_jsonrpc(method, params) or {}
            item = response.get('result', {}).get(self.jrpc_key)

            return [self.make_item(item)]

        items = [
            {'url': li.getPath(), 'listitem': li, 'isFolder': li.getProperty('isfolder').lower() == 'true'}
            for li in _get_items() if li]

        self.add_items(items)


class ListGetMovieSetDetails(ListGetItemDetails):
    jrpc_method = "VideoLibrary.GetMovieSetDetails"
    jrpc_properties = ["title", "plot", "playcount", "fanart", "thumbnail", "art"]
    jrpc_id = "setid"
    jrpc_key = "setdetails"


class ListGetMovieDetails(ListGetItemDetails):
    jrpc_method = "VideoLibrary.GetMovieDetails"
    jrpc_properties = ["title", "plot", "genre", "director", "writer", "studio", "cast", "country", "fanart", "thumbnail", "tag", "art", "ratings"]
    jrpc_id = "movieid"
    jrpc_key = "moviedetails"


class ListGetTVShowDetails(ListGetItemDetails):
    jrpc_method = "VideoLibrary.GetTVShowDetails"
    jrpc_properties = ["title", "plot", "genre", "studio", "cast", "fanart", "thumbnail", "tag", "art", "ratings", "runtime"]
    jrpc_id = "tvshowid"
    jrpc_key = "tvshowdetails"


class ListGetSeasonDetails(ListGetItemDetails):
    jrpc_method = "VideoLibrary.GetSeasonDetails"
    jrpc_properties = ["title", "plot", "fanart", "thumbnail", "tvshowid", "art"]
    jrpc_id = "seasonid"
    jrpc_key = "seasondetails"


class ListGetEpisodeDetails(ListGetItemDetails):
    jrpc_method = "VideoLibrary.GetEpisodeDetails"
    jrpc_properties = ["title", "plot", "writer", "director", "cast", "fanart", "thumbnail", "tvshowid", "art", "seasonid", "ratings"]
    jrpc_id = "episodeid"
    jrpc_key = "episodedetails"


class ListGetPlayerStreams(Container):
    def get_directory(self, stream_type=None, **kwargs):
        from jurialmunkey.jsnrpc import get_jsonrpc

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


class ListSetPlayerStreams(Container):
    def get_directory(self, stream_type=None, stream_index=None, **kwargs):
        if not stream_type or stream_index is None:
            return
        if stream_type == 'audio':
            from resources.lib.method import set_player_audiostream
            set_player_audiostream(stream_index)
            return
        if stream_type == 'subtitle':
            from resources.lib.method import set_player_subtitle
            set_player_subtitle(stream_index)
            return


class Plugin():
    def __init__(self, handle, paramstring):
        # plugin:// params configuration
        from jurialmunkey.parser import parse_paramstring
        self.handle = handle  # plugin:// handle
        self.paramstring = paramstring  # plugin://plugin.video.themoviedb.helper?paramstring
        self.params = parse_paramstring(self.paramstring)  # paramstring dictionary
        self.routes = {
            'get_player_streams': ListGetPlayerStreams,
            'set_player_streams': ListSetPlayerStreams,
            'get_dbitem_movieset_details': ListGetMovieSetDetails,
            'get_dbitem_movie_details': ListGetMovieDetails,
            'get_dbitem_tvshow_details': ListGetTVShowDetails,
            'get_dbitem_season_details': ListGetSeasonDetails,
            'get_dbitem_episode_details': ListGetEpisodeDetails,
        }

    def get_container(self, info):
        return self.routes[info]

    def get_directory(self):
        container = self.get_container(self.params.get('info'))(self.handle, self.paramstring, **self.params)
        return container.get_directory(**self.params)

    def run(self):
        self.get_directory()
