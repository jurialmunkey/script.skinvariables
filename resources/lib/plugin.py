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
        'get_filter_dir': {
            'module_name': 'resources.lib.lists.filterdir',
            'import_attr': 'ListGetFilterDir'},
    }

    def __init__(self, handle, paramstring):
        # plugin:// params configuration
        from jurialmunkey.parser import parse_paramstring
        self.handle = handle  # plugin:// handle
        self.paramstring = paramstring  # plugin://plugin.video.themoviedb.helper?paramstring
        self.params = parse_paramstring(self.paramstring)  # paramstring dictionary

    def get_container(self, info):
        from jurialmunkey.modimp import importmodule
        return importmodule(**self.routes[info])

    def get_directory(self):
        container = self.get_container(self.params.get('info'))(self.handle, self.paramstring, **self.params)
        return container.get_directory(**self.params)

    def run(self):
        self.get_directory()
