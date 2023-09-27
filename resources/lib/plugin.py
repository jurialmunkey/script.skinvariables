# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

class Plugin():
    routes = {
        'get_player_streams': {
            'module_name': 'resources.lib.lists.playerstreams',
            'import_attr': 'ListGetPlayerStreams'},
        'set_player_streams': {
            'module_name': 'resources.lib.lists.playerstreams',
            'import_attr': 'ListSetPlayerStreams'},
        'get_dbitem_movieset_details': {
            'module_name': 'resources.lib.lists.rpcdetails',
            'import_attr': 'ListGetMovieSetDetails'},
        'get_dbitem_movie_details': {
            'module_name': 'resources.lib.lists.rpcdetails',
            'import_attr': 'ListGetMovieDetails'},
        'get_dbitem_tvshow_details': {
            'module_name': 'resources.lib.lists.rpcdetails',
            'import_attr': 'ListGetTVShowDetails'},
        'get_dbitem_season_details': {
            'module_name': 'resources.lib.lists.rpcdetails',
            'import_attr': 'ListGetSeasonDetails'},
        'get_dbitem_episode_details': {
            'module_name': 'resources.lib.lists.rpcdetails',
            'import_attr': 'ListGetEpisodeDetails'},
        'get_dbitem_addon_details': {
            'module_name': 'resources.lib.lists.rpcdetails',
            'import_attr': 'ListGetAddonDetails'},
        'get_number_sum': {
            'module_name': 'resources.lib.lists.koditools',
            'import_attr': 'ListGetNumberSum'},
        'get_split_string': {
            'module_name': 'resources.lib.lists.koditools',
            'import_attr': 'ListGetSplitString'},
        'get_encoded_string': {
            'module_name': 'resources.lib.lists.koditools',
            'import_attr': 'ListGetEncodedString'},
        'get_file_exists': {
            'module_name': 'resources.lib.lists.koditools',
            'import_attr': 'ListGetFileExists'},
        'get_filter_dir': {
            'module_name': 'resources.lib.lists.filterdir',
            'import_attr': 'ListGetFilterDir'},
        'get_container_labels': {
            'module_name': 'resources.lib.lists.filterdir',
            'import_attr': 'ListGetContainerLabels'},
    }

    def __init__(self, handle, paramstring):
        # plugin:// params configuration
        from jurialmunkey.parser import parse_paramstring
        self.handle = handle  # plugin:// handle
        self.paramstring, *secondary_params = paramstring.split('&&')  # plugin://plugin.video.themoviedb.helper?paramstring
        self.params = parse_paramstring(self.paramstring)  # paramstring dictionary
        if not secondary_params:
            return
        from urllib.parse import unquote_plus
        self.params['paths'] = [unquote_plus(i) for i in secondary_params]

    def get_container(self, info):
        from jurialmunkey.modimp import importmodule
        return importmodule(**self.routes[info])

    def get_directory(self):
        container = self.get_container(self.params.get('info'))(self.handle, self.paramstring, **self.params)
        return container.get_directory(**self.params)

    def run(self):
        self.get_directory()
