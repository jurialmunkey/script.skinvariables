# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sys
import xbmcplugin
from tmdbhelper.parser import parse_paramstring
from resources.lib.jsonrpc import get_player_streams
from resources.lib.method import set_player_subtitle, set_player_audiostream


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
        if not stream_type:
            return
        items = [
            {'url': li.getPath(), 'listitem': li, 'isFolder': li.getProperty('isfolder').lower() == 'true'}
            for li in get_player_streams(stream_type) if li]
        self.add_items(items)

    def run(self):
        if not self.params:
            return
        if self.params.get('info') not in self.routes:
            return
        self.routes[self.params['info']](**self.params)
