# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import operator
from xbmcgui import ListItem
from resources.lib.container import Container
from infotagger.listitem import ListItemInfoTag
from jurialmunkey.parser import split_items

DIRECTORY_PROPERTIES_BASIC = ["title", "art", "file"]

DIRECTORY_PROPERTIES_VIDEO = [
    "genre", "year", "rating", "playcount", "director", "trailer", "tagline", "plot", "plotoutline", "originaltitle", "lastplayed", "writer",
    "studio", "mpaa", "country", "premiered", "runtime", "set", "streamdetails", "top250", "votes", "firstaired", "season", "episode", "showtitle",
    "sorttitle", "thumbnail", "uniqueid", "dateadded", "customproperties"]

DIRECTORY_PROPERTIES_MUSIC = [
    "artist", "albumartist", "genre", "year", "rating", "album", "track", "duration", "lastplayed", "studio", "mpaa",
    "disc", "description", "theme", "mood", "style", "albumlabel", "sorttitle", "uniqueid", "dateadded", "customproperties"]

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
        _exclude = True
        for fv in split_items(filter_value):
            _exclude = True
            if filter_key in il:
                _exclude = False
                if is_filtered(il, filter_key, fv, operator_type=filter_operator):
                    _exclude = True
                    continue
            if filter_key in ip:
                _exclude = False
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
    def get_directory(self, paths=None, library=None, no_label_dupes=False, **kwargs):
        from jurialmunkey.jsnrpc import get_directory

        if not paths:
            return

        def _get_filters(filters):
            all_filters = {}
            filter_name = ['filter_key', 'filter_value', 'filter_operator', 'exclude_key', 'exclude_value', 'exclude_operator']

            for k, v in filters.items():
                key, num = k, '0'
                if '__' in k:
                    key, num = k.split('__', 1)
                if key not in filter_name:
                    continue
                dic = all_filters.setdefault(num, {})
                dic[key] = v

            return all_filters

        mediatypes = {}
        added_items = []
        all_filters = _get_filters(kwargs)
        directory_properties = DIRECTORY_PROPERTIES_BASIC
        directory_properties += {
            'video': DIRECTORY_PROPERTIES_VIDEO,
            'music': DIRECTORY_PROPERTIES_VIDEO}.get(library) or []

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
            mediatype = 'video' if mediatype in ['unknown', ''] else mediatype

            infolabels = {INFOLABEL_MAP[k]: v for k, v in i.items() if v and k in INFOLABEL_MAP and v != -1}
            infolabels['title'] = label
            infolabels['mediatype'] = mediatype

            uniqueids = i.get('uniqueid') or {}
            streamdetails = i.get('streamdetails') or {}
            infoproperties = i.get('customproperties') or {}

            for _, filters in all_filters.items():
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

            if not no_label_dupes:
                return item

            if label in added_items:
                return

            added_items.append(label)
            return item

        items = []
        for path in paths:
            directory = get_directory(path, directory_properties)
            items += [j for j in (_make_item(i) for i in directory if i) if j]

        plugin_category = ''
        container_content = f'{max(mediatypes, key=lambda key: mediatypes[key])}s' if mediatypes else ''
        self.add_items(items, container_content=container_content, plugin_category=plugin_category)


class ListGetContainerLabels(Container):
    def get_directory(self, containers, infolabel, numitems, separator=' / ', filter_value=None, filter_operator=None, exclude_value=None, exclude_operator=None, **kwargs):
        from xbmc import getInfoLabel as get_infolabel

        filters = {
            'filter_key': 'title',
            'filter_value': filter_value,
            'filter_operator': filter_operator,
            'exclude_key': 'title',
            'exclude_value': exclude_value,
            'exclude_operator': exclude_operator,
        }

        added_items = []

        def _make_item(title):
            if title in added_items:
                return

            if is_excluded({'infolabels': {'title': title}}, **filters):
                return

            listitem = ListItem(label=title, label2='', path='', offscreen=True)
            item = {'url': '', 'listitem': listitem, 'isFolder': True}

            added_items.append(title)
            return item

        items = []
        for container in containers.split():
            numitems = int(get_infolabel(f'Container({container}).NumItems') or 0)
            if not numitems:
                continue
            for x in range(numitems):
                titles = get_infolabel(f'Container({container}).ListItemAbsolute({x}).{infolabel}')
                if not titles:
                    continue
                for title in titles.split(separator):
                    item = _make_item(title)
                    if not item:
                        continue
                    items.append(item)

        self.add_items(items)
