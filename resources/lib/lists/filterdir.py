# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import operator
from xbmcgui import ListItem
from resources.lib.container import Container
from infotagger.listitem import ListItemInfoTag
from jurialmunkey.parser import split_items


DIRECTORY_PROPERTIES = [
    "title", "artist", "albumartist", "genre", "year", "rating", "album", "track", "duration", "comment", "lyrics",
    "musicbrainztrackid", "musicbrainzartistid", "musicbrainzalbumid", "musicbrainzalbumartistid", "playcount", "fanart",
    "director", "trailer", "tagline", "plot", "plotoutline", "originaltitle", "lastplayed", "writer", "studio", "mpaa",
    "cast", "country", "imdbnumber", "premiered", "productioncode", "runtime", "set", "showlink", "streamdetails", "top250",
    "votes", "firstaired", "season", "episode", "showtitle", "thumbnail", "file", "resume", "artistid", "albumid", "tvshowid",
    "setid", "watchedepisodes", "disc", "tag", "art", "genreid", "displayartist", "albumartistid", "description", "theme",
    "mood", "style", "albumlabel", "sorttitle", "episodeguide", "uniqueid", "dateadded", "size", "lastmodified", "mimetype",
    "specialsortseason", "specialsortepisode", "sortartist", "musicbrainzreleasegroupid", "isboxset", "totaldiscs", "disctitle",
    "releasedate", "originaldate", "bpm", "bitrate", "samplerate", "channels", "datemodified", "datenew", "customproperties",
    "albumduration"]

INFOLABEL_MAP = {
    "title": "title",
    "artist": "artist",
    "albumartist": "albumartist",
    "genre": "genre",
    "year": "year",
    "rating": "rating",
    "album": "album",
    "track": "track",
    "duration": "duration",
    "playcount": "playcount",
    "director": "director",
    "trailer": "trailer",
    "tagline": "tagline",
    "plot": "plot",
    "plotoutline": "plotoutline",
    "originaltitle": "originaltitle",
    "lastplayed": "lastplayed",
    "writer": "writer",
    "studio": "studio",
    "mpaa": "mpaa",
    "country": "country",
    "premiered": "premiered",
    "set": "set",
    "top250": "top250",
    "votes": "votes",
    "firstaired": "firstaired",
    "season": "season",
    "episode": "episode",
    "showtitle": "tvshowtitle",
    "sorttitle": "sorttitle",
    "episodeguide": "episodeguide",
    "dateadded": "dateadded",
    "id": "dbid",
}


def is_excluded(item, filter_key=None, filter_value=None, filter_operator=None, exclude_key=None, exclude_value=None, exclude_operator=None):
    """ Checks if item should be excluded based on filter/exclude values
    Values can optional be a dict which contains module, method, and kwargs
    """
    def is_filtered(d, k, v, exclude=False, operator_type=None):
        comp = getattr(operator, operator_type or 'contains')
        boolean = False if exclude else True  # Flip values if we want to exclude instead of include
        if k and v and k in d and comp(str(d[k]).lower(), str(v).lower()):
            boolean = exclude
        return boolean

    if not item:
        return

    il, ip = item.get('infolabels', {}), item.get('infoproperties', {})

    if filter_key and filter_value:
        _exclude = False
        for fv in split_items(filter_value):
            _exclude = False
            if filter_key in il:
                if is_filtered(il, filter_key, fv, operator_type=filter_operator):
                    _exclude = True
                    continue
            if filter_key in ip:
                if is_filtered(ip, filter_key, fv, operator_type=filter_operator):
                    _exclude = True
                    continue
            if not _exclude:
                break
        if _exclude:
            return True

    if exclude_key and exclude_value:
        for ev in split_items(exclude_value):
            if exclude_key in il:
                if is_filtered(il, exclude_key, ev, True, operator_type=exclude_operator):
                    return True
            if exclude_key in ip:
                if is_filtered(ip, exclude_key, ev, True, operator_type=exclude_operator):
                    return True


class ListGetFilterDir(Container):
    def get_directory(self, path=None, **kwargs):
        from jurialmunkey.jsnrpc import get_directory

        if not path:
            return

        directory = get_directory(path, DIRECTORY_PROPERTIES)
        mediatypes = {}

        # from resources.lib.kodiutils import kodi_log
        # kodi_log(f'MYDIR: {path}\n{directory}', 1)

        filters = {
            'filter_key': kwargs.get('filter_key', None),
            'filter_value': kwargs.get('filter_value', None),
            'filter_operator': kwargs.get('filter_operator', None),
            'exclude_key': kwargs.get('exclude_key', None),
            'exclude_value': kwargs.get('exclude_value', None),
            'exclude_operator': kwargs.get('exclude_operator', None)}

        def _get_label(i):
            if i.get('title'):
                return i['title']
            if i.get('label'):
                return i['label']
            return ''

        def _make_item(i):
            label = _get_label(i)
            label2 = ''
            path = i.get('file') or ''
            mediatype = i.get('type') or ''
            mediatype = '' if mediatype in ['unknown'] else mediatype

            infolabels = {INFOLABEL_MAP[k]: v for k, v in i.items() if v and k in INFOLABEL_MAP and v != -1}
            infolabels['title'] = label
            infolabels['mediatype'] = mediatype

            uniqueids = i.get('uniqueid') or {}
            streamdetails = i.get('streamdetails') or {}
            infoproperties = i.get('customproperties') or {}

            if is_excluded({'infolabels': infolabels, 'infoproperties': infoproperties}, **filters):
                return

            if mediatype:
                mediatypes[mediatype] = mediatypes.get(mediatype, 0) + 1

            listitem = ListItem(label=label, label2='', path=path, offscreen=True)
            listitem.setLabel2(label2)
            listitem.setArt(i.get('art', {}))

            info_tag = ListItemInfoTag(listitem)
            info_tag.set_info(infolabels)
            info_tag.set_unique_ids(uniqueids)
            info_tag.set_stream_details(streamdetails)

            listitem.setProperties(infoproperties)

            item = {'url': path, 'listitem': listitem, 'isFolder': True}
            return item

        items = [j for j in (_make_item(i) for i in directory if i) if j]

        plugin_category = ''
        container_content = f'{max(mediatypes, key=lambda key: mediatypes[key])}s' if mediatypes else ''
        self.add_items(items, container_content=container_content, plugin_category=plugin_category)
