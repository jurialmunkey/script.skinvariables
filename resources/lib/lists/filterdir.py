# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import operator
from xbmcgui import ListItem
from resources.lib.container import Container
from resources.lib.method import set_to_windowprop
from infotagger.listitem import ListItemInfoTag
from jurialmunkey.parser import split_items

DIRECTORY_PROPERTIES_BASIC = ["title", "art", "file", "fanart"]

DIRECTORY_PROPERTIES_VIDEO = [
    "genre", "year", "rating", "playcount", "director", "trailer", "tagline", "plot", "plotoutline", "originaltitle", "lastplayed", "writer",
    "studio", "mpaa", "country", "premiered", "runtime", "set", "streamdetails", "top250", "votes", "firstaired", "season", "episode", "showtitle",
    "tvshowid", "setid", "sorttitle", "thumbnail", "uniqueid", "dateadded", "customproperties"]

DIRECTORY_PROPERTIES_MUSIC = [
    "artist", "albumartist", "genre", "year", "rating", "album", "track", "duration", "lastplayed", "studio", "mpaa",
    "disc", "description", "theme", "mood", "style", "albumlabel", "sorttitle", "uniqueid", "dateadded", "customproperties",
    "totaldiscs", "disctitle", "releasedate", "originaldate", "bpm", "bitrate", "samplerate", "channels"]

INFOLABEL_MAP = {
    "title": "title",
    "artist": "artist",
    "albumartist": "albumartist",
    "genre": "genre",
    "year": "year",
    "rating": "rating",
    "album": "album",
    "track": "tracknumber",
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
    "firstaired": "aired",
    "season": "season",
    "episode": "episode",
    "showtitle": "tvshowtitle",
    "sorttitle": "sorttitle",
    "episodeguide": "episodeguide",
    "dateadded": "date",
    "id": "dbid",
}

INFOPROPERTY_MAP = {
    "disctitle": "disctitle",
    "releasedate": "releasedate",
    "originaldate": "originaldate",
    "bpm": "bpm",
    "bitrate": "bitrate",
    "samplerate": "samplerate",
    "channels": "channels",
    "totaldiscs": "totaldiscs",
    "disc": "disc",
    "description": "description",
    "theme": "theme",
    "mood": "mood",
    "style": "style",
    "albumlabel": "albumlabel",
    "tvshowid": "tvshow.dbid",
    "setid": "set.dbid"
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


class MetaItemJSONRPC():
    def __init__(self, meta, dbtype='video'):
        self.meta = meta or {}
        self.dbtype = dbtype

    @property
    def label(self):
        if self.meta.get('title'):
            return self.meta['title']
        if self.meta.get('label'):
            return self.meta['label']
        return ''

    @property
    def path(self):
        if self.meta.get('file'):
            return self.meta['file']
        return ''

    @property
    def mediatype(self):
        mediatype = self.meta.get('type') or ''
        if mediatype in ['unknown', '']:
            return self.dbtype
        return mediatype

    @property
    def infolabels(self):
        return {INFOLABEL_MAP[k]: v for k, v in self.meta.items() if v and k in INFOLABEL_MAP and v != -1}

    @property
    def infoproperties(self):
        infoproperties = {INFOPROPERTY_MAP[k]: str(v) for k, v in self.meta.items() if v and k in INFOPROPERTY_MAP and v != -1}
        infoproperties.update({k: str(v) for k, v in (self.meta.get('customproperties') or {}).items()})
        return infoproperties

    @property
    def uniqueids(self):
        return self.meta.get('uniqueid') or {}

    @property
    def streamdetails(self):
        return self.meta.get('streamdetails') or {}

    @property
    def artwork(self):
        artwork = self.meta.get('art') or {}
        remap = (
            ('thumb', 'thumb'),
            ('fanart', 'fanart'))
        for a, k in remap:
            if self.meta.get(k) and not artwork.get(a):
                artwork[a] = self.meta[k]
        return artwork

    @property
    def filetype(self):
        return self.meta.get('filetype')


class ListItemJSONRPC():
    def __init__(self, meta, library='video', dbtype='video'):
        self.meta = MetaItemJSONRPC(meta, dbtype)
        self.is_folder = True
        self.library = library or 'video'
        self.infolabels = self.meta.infolabels
        self.infoproperties = self.meta.infoproperties
        self.uniqueids = self.meta.uniqueids
        self.streamdetails = self.meta.streamdetails
        self.artwork = self.meta.artwork
        self.filetype = self.meta.filetype
        self.mediatype = self.meta.mediatype
        self.path = self.meta.path
        self.label = self.meta.label
        self.label2 = ''

    @property
    def mediatype(self):
        return self._mediatype

    @mediatype.setter
    def mediatype(self, value: str):
        self._mediatype = value
        self.infolabels['mediatype'] = value

    @property
    def infolabels(self):
        return self._infolabels

    @infolabels.setter
    def infolabels(self, value):
        self._infolabels = value
        self.fix_music_infolabels()

    def fix_music_infolabels(self):
        # Fix some incompatible type returns from JSON RPC to info_tag in music library
        if self.library != 'music':
            return
        for a in ('artist', 'albumartist', 'album'):
            if not isinstance(self.infolabels.get(a), list):
                continue
            self.infolabels[a] = ' / '.join(self.infolabels[a])

    @property
    def artwork(self):
        return self._artwork

    @artwork.setter
    def artwork(self, value):
        self._artwork = value

        def _map_artwork(key: str, names: tuple):
            if self._artwork.get(key):
                return self._artwork[key]
            for a in names:
                if self._artwork.get(a):
                    return self._artwork[a]
            return ''

        if self.library == 'music':
            parents = ('album', 'albumartist', 'artist')
            for k in ('thumb', 'fanart', 'clearlogo'):
                self._artwork[k] = _map_artwork(k, (f'{parent}.{k}' for parent in parents))

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value
        self.is_folder = True

        if self.filetype == 'file':
            self.is_folder = False
            self.infoproperties['isPlayable'] = 'true'
            return

        if self._path.startswith('videodb://'):
            return

        if self._path.startswith('plugin://'):
            return

        if self.mediatype == 'tvshow' and self.infolabels.get('dbid'):
            self._path = f'videodb://tvshows/titles/{self.infolabels["dbid"]}/'
            return

        if self.mediatype == 'season' and self.infolabels.get('tvshow.dbid'):
            self._path = f'videodb://tvshows/titles/{self.infoproperties["tvshow.dbid"]}/{self.infolabels["season"]}/'
            return

    @property
    def listitem(self):
        self._listitem = ListItem(label=self.label, label2=self.label2, path=self.path, offscreen=True)
        self._listitem.setLabel2(self.label2)
        self._listitem.setArt(self.artwork)

        self._info_tag = ListItemInfoTag(self._listitem, self.library)
        self._info_tag.set_info(self.infolabels)
        if self.library == 'video':
            self._info_tag.set_unique_ids(self.uniqueids)
            self._info_tag.set_stream_details(self.streamdetails)

        self._listitem.setProperties(self.infoproperties)
        return self._listitem


class ListGetFilterDir(Container):
    def get_directory(self, paths=None, library=None, no_label_dupes=False, dbtype=None, **kwargs):
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
            'music': DIRECTORY_PROPERTIES_MUSIC}.get(library) or []

        def _make_item(i):
            listitem_jsonrpc = ListItemJSONRPC(i, library=library, dbtype=dbtype)
            listitem_jsonrpc.infolabels['title'] = listitem_jsonrpc.label

            for _, filters in all_filters.items():
                if is_excluded({'infolabels': listitem_jsonrpc.infolabels, 'infoproperties': listitem_jsonrpc.infoproperties}, **filters):
                    return

            if listitem_jsonrpc.mediatype:
                mediatypes[listitem_jsonrpc.mediatype] = mediatypes.get(listitem_jsonrpc.mediatype, 0) + 1

            item = {'url': listitem_jsonrpc.path, 'listitem': listitem_jsonrpc.listitem, 'isFolder': listitem_jsonrpc.is_folder}

            if not no_label_dupes:
                return item

            if listitem_jsonrpc.label in added_items:
                return

            added_items.append(listitem_jsonrpc.label)
            return item

        items = []
        for path in paths:
            directory = get_directory(path, directory_properties)
            items += [j for j in (_make_item(i) for i in directory if i) if j]

        plugin_category = ''
        container_content = f'{max(mediatypes, key=lambda key: mediatypes[key])}s' if mediatypes else ''
        self.add_items(items, container_content=container_content, plugin_category=plugin_category)


class ListGetContainerLabels(Container):
    def get_directory(
            self, containers, infolabel, numitems=None, thumb=None, label2=None, separator=' / ',
            filter_value=None, filter_operator=None, exclude_value=None, exclude_operator=None,
            window_prop=None, window_id=None,
            **kwargs):
        import xbmc

        filters = {
            'filter_key': 'title',
            'filter_value': filter_value,
            'filter_operator': filter_operator,
            'exclude_key': 'title',
            'exclude_value': exclude_value,
            'exclude_operator': exclude_operator,
        }

        added_items = []

        def _make_item(title, image, label):
            if title in added_items:
                return

            if is_excluded({'infolabels': {'title': title}}, **filters):
                return

            listitem = ListItem(label=title, label2=label or '', path='', offscreen=True)
            listitem.setArt({'icon': image or '', 'thumb': image or ''})
            item = {'url': '', 'listitem': listitem, 'isFolder': True}

            added_items.append(title)
            return item

        items = []
        for container in containers.split():
            numitems = int(xbmc.getInfoLabel(f'Container({container}).NumItems') or 0)
            if not numitems:
                continue
            for x in range(numitems):
                image = xbmc.getInfoLabel(f'Container({container}).ListItemAbsolute({x}).{thumb}') if thumb else ''
                label = xbmc.getInfoLabel(f'Container({container}).ListItemAbsolute({x}).{label2}') if label2 else ''
                for il in infolabel.split():
                    titles = xbmc.getInfoLabel(f'Container({container}).ListItemAbsolute({x}).{il}')
                    if not titles:
                        continue
                    for title in titles.split(separator):
                        item = _make_item(title, image, label)
                        if not item:
                            continue
                        items.append(item)

        self.add_items(items)

        if not window_prop or not added_items:
            return

        for x, i in enumerate(added_items):
            set_to_windowprop(i, x, window_prop, window_id)

        xbmc.executebuiltin(f'SetProperty({window_prop},{" / ".join(added_items)}{f",{window_id}" if window_id else ""})')
