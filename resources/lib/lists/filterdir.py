# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import operator
from xbmcgui import ListItem, Dialog
from infotagger.listitem import ListItemInfoTag
from jurialmunkey.parser import split_items
from jurialmunkey.litems import Container
from jurialmunkey.window import set_to_windowprop, WindowProperty
from resources.lib.kodiutils import kodi_log
import jurialmunkey.thread as jurialmunkey_thread


class ParallelThread(jurialmunkey_thread.ParallelThread):
    thread_max = 50

    @staticmethod
    def kodi_log(msg, level=0):
        kodi_log(msg, level)


DIRECTORY_PROPERTIES_BASIC = ["title", "art", "file", "fanart"]

DIRECTORY_PROPERTIES_VIDEO = [
    "genre", "year", "rating", "playcount", "director", "trailer", "tagline", "plot", "plotoutline", "originaltitle", "lastplayed", "writer",
    "studio", "mpaa", "country", "premiered", "runtime", "set", "streamdetails", "top250", "votes", "firstaired", "season", "episode", "showtitle",
    "tvshowid", "setid", "sorttitle", "thumbnail", "uniqueid", "dateadded", "customproperties"]

DIRECTORY_PROPERTIES_MUSIC = [
    "artist", "albumartist", "genre", "year", "rating", "album", "track", "duration", "lastplayed", "studio", "mpaa",
    "disc", "description", "theme", "mood", "style", "albumlabel", "sorttitle", "uniqueid", "dateadded", "customproperties",
    "totaldiscs", "disctitle", "releasedate", "originaldate", "bpm", "bitrate", "samplerate", "channels"]


SFD_ANOTHERPATH_HEADING = 'Add another path?'
SFD_ANOTHERPATH_MESSAGE = 'Do you want to add another path?'
SFD_FILENAMEINPUT_HEADING = 'Enter name'
SFD_SORTBY_METHODS = [
    "none", "title", "genre", "year", "rating", "playcount", "director", "trailer", "tagline", "plot", "originaltitle", "lastplayed", "writer",
    "studio", "mpaa", "country", "premiered", "top250", "votes", "tvshowtitle", "custom"
]
SFD_SORTHOW_HEADING = 'Sort direction'
SFD_SORTHOW_MESSAGE = 'Select sort direction'
SFD_SORTBY_HEADING = 'Method for {}'
SFD_SORTBY_INPUT_HEADING = 'Enter custom {} infolabel or property name'
SFD_SORTBY_VALUE_HEADING = 'Enter custom {} value to match'
SFD_FILTEROPERATOR_HEADING = 'Operator for {}'


STANDARD_OPERATORS = {
    'contains': 'Contains',
    'lt': 'Less than <',
    'le': 'Less than or equal <=',
    'eq': 'Equal ==',
    'ne': 'Not equal !=',
    'ge': 'Greater than or equal >=',
    'gt': 'Greater than >',
}

META_DELPATH_MESSAGE = 'Are you sure you want to remove this path?\n{}'
META_DELPATH_HEADING = 'Remove path'
META_EDITFILTERS_HEADING = 'Edit filters'
META_SAVECHANGES_HEADING = 'Save changes'
META_SAVECHANGES_MESSAGE = 'Do you want to save your changes?'
META_DELETEFILE_HEADING = 'Delete file'
META_DELETEFILE_MESSAGE = 'Are you sure you want to delete this file?\n[COLOR=red][B]WARNING[/B][/COLOR]: This action cannot be undone.'


def update_global_property_versions():
    """ Add additional properties from newer versions of JSON RPC """

    from jurialmunkey.jsnrpc import get_jsonrpc

    response = get_jsonrpc("JSONRPC.Version")
    version = (
        response['result']['version']['major'],
        response['result']['version']['minor'],
        response['result']['version']['patch'],
    )

    if version >= (13, 3, 0):
        DIRECTORY_PROPERTIES_MUSIC.append('songvideourl')  # Added in 13.3.0 of JSON RPC


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
    "songvideourl": "songvideourl",
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
    "setid": "set.dbid",
    "songvideourl": "songvideourl",
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

        if '://' in self._path:
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


class ListGetFilterFiles(Container):
    def get_directory(self, filepath=None, **kwargs):
        from resources.lib.shortcuts.futils import get_files_in_folder

        basepath = 'plugin://script.skinvariables/'
        filepath = filepath or 'special://profile/addon_data/script.skinvariables/nodes/dynamic/'

        def _make_item(i):
            editpath = f'{basepath}?info=set_filter_dir&filepath=special://profile/addon_data/script.skinvariables/nodes/dynamic/{i}'
            itempath = f'{basepath}?info=get_params_file&path=special://profile/addon_data/script.skinvariables/nodes/dynamic/{i}'
            li = ListItem(label=f'{i}', path=itempath)
            li.addContextMenuItems([('Edit filters', f'RunPlugin({editpath})')])
            return (itempath, li, True)

        def _add_new_item():
            path = f'{basepath}?info=set_filter_dir'
            return (path, ListItem(label='Add new...', path=path), True)

        files = get_files_in_folder(filepath, r'.*\.json')
        items = [_make_item(i) for i in files if i] + [_add_new_item()]

        plugin_category = ''
        container_content = ''
        self.add_items(items, container_content=container_content, plugin_category=plugin_category)


class MetaFilterDir():
    def __init__(self, library='video', filepath=None):
        self.library = library
        self.filepath = filepath

    @property
    def meta(self):
        try:
            return self._meta
        except AttributeError:
            self._meta = self.get_files_meta()
            return self._meta

    def get_blank_meta(self):
        return {
            'info': 'get_filter_dir',
            'library': self.library,
            'paths': []
        }

    def get_files_meta(self):
        if not self.filepath:
            return self.get_blank_meta()
        from resources.lib.shortcuts.futils import read_meta_from_file
        return read_meta_from_file(self.filepath) or self.get_blank_meta()

    @staticmethod
    def get_new_path():
        from resources.lib.shortcuts.browser import GetDirectoryBrowser
        with WindowProperty(('IsSkinShortcut', 'True')):
            item = GetDirectoryBrowser(use_rawpath=True).get_directory(path='library://video/')  # TODO: Add some choice of library
        try:
            path, target = item['path'], item['target']
        except (TypeError, KeyError):
            return
        if not target:  # TODO: Add some validation we have correct library
            pass
        return path

    @staticmethod
    def get_new_method(heading, customheading, methods=SFD_SORTBY_METHODS):
        x = Dialog().select(heading, methods)
        if x == -1:
            return None
        v = methods[x]
        if v == 'custom':
            return Dialog().input(heading=customheading)
        if v == 'none':
            return ''
        return v

    def get_new_suffix(self, prefix):
        import random
        existing_filter_suffix = [k.replace(f'{prefix}_key__', '') for k in self.meta.keys() if k.startswith(f'{prefix}_key__')]  # Suffix prefixed by double underscore

        def get_suffix():
            suffix = f'{random.randrange(16**8):08x}'
            if suffix not in existing_filter_suffix:
                return f'_{suffix}'  # Suffix prefixed by double underscore but one will be added when joining so only add one now
            return get_suffix()

        return get_suffix()

    def toggle_randomise(self):
        from jurialmunkey.parser import boolean
        if boolean(self.meta.get('randomise', False)):
            del self.meta['randomise']
            return
        self.meta['randomise'] = 'true'

    def del_path(self, value):
        x = next(x for x, i in enumerate(self.meta['paths']) if i == value)
        del self.meta['paths'][x]

    def add_new_path(self, update=None):
        path = self.get_new_path()
        if update:
            x = next(x for x, i in enumerate(self.meta['paths']) if i == update)
            self.meta['paths'][x] = path
            self.meta['paths'] = [i for i in self.meta['paths'] if i]  # Remove any null paths
            return
        if path is None:
            return self.meta['paths']
        self.meta['paths'].append(path)
        if Dialog().yesno(SFD_ANOTHERPATH_HEADING, SFD_ANOTHERPATH_MESSAGE):
            return self.add_new_path()
        return self.meta['paths']

    def add_new_sort_how(self):
        self.meta['sort_how'] = 'desc' if Dialog().yesno(
            SFD_SORTHOW_HEADING.format('sort'),
            SFD_SORTHOW_MESSAGE.format('sort'),
            yeslabel='Descending',
            nolabel='Ascending'
        ) else 'asc'

    def add_new_sort_by(self):
        sort_by = self.get_new_method(
            SFD_SORTBY_HEADING.format('sort'),
            SFD_SORTBY_INPUT_HEADING.format('sort')
        )
        if sort_by is None:
            return
        self.meta['sort_by'] = sort_by

    def add_new_sort(self):
        self.add_new_sort_by()
        if not self.meta['sort_by']:
            return
        self.add_new_sort_how()

    def del_filter(self, prefix='filter', suffix='', keys=('key', 'value', 'operator')):
        key_names = ['_'.join(filter(None, [prefix, k, suffix])) for k in keys]
        for k in key_names:
            try:
                del self.meta[k]
            except KeyError:
                pass

    def add_new_filter_operator(self, prefix='filter', suffix=''):
        choices = [(k, v) for k, v in STANDARD_OPERATORS.items()]
        x = Dialog().select(SFD_FILTEROPERATOR_HEADING.format(prefix), [i for _, i in choices])
        if x == -1:
            return
        filter_operator = choices[x][0]
        k = '_'.join(filter(None, [prefix, 'operator', suffix]))
        self.meta[k] = filter_operator
        return filter_operator

    def add_new_filter_key(self, prefix='filter', suffix=''):
        filter_key = self.get_new_method(
            SFD_SORTBY_HEADING.format(prefix),
            SFD_SORTBY_INPUT_HEADING.format(prefix)
        )
        if filter_key is None:
            return
        if filter_key == '':
            self.del_filter(prefix, suffix)
            return
        k = '_'.join(filter(None, [prefix, 'key', suffix]))
        self.meta[k] = filter_key
        return filter_key

    def add_new_filter_value(self, prefix='filter', suffix=''):
        k = '_'.join(filter(None, [prefix, 'key', suffix]))
        if not self.meta.get(k):
            self.del_filter(prefix, suffix)
            return
        filter_value = Dialog().input(heading=SFD_SORTBY_VALUE_HEADING.format(prefix))
        if not filter_value:
            self.del_filter(prefix, suffix)
            return
        k = '_'.join(filter(None, [prefix, 'value', suffix]))
        self.meta[k] = filter_value
        return filter_value

    def add_new_filter(self, prefix='filter', suffix=''):
        if not self.add_new_filter_key(prefix, suffix):
            return
        self.add_new_filter_operator(prefix, suffix)
        self.add_new_filter_value(prefix, suffix)

    def write_meta(self, filename=None):
        from resources.lib.shortcuts.futils import FILEUTILS, validify_filename
        filename = filename or Dialog().input(heading=SFD_FILENAMEINPUT_HEADING)
        filename = validify_filename(filename)
        if not filename:  # TODO: Ask user if they are sure they dont want to make the file.
            return
        filename = f'{filename}.json'
        FILEUTILS.dumps_to_file(self.meta, folder='dynamic', filename=filename, indent=4)  # TODO: Make sure we dont overwrite?
        return filename

    def delete_meta(self):
        if not self.filepath:
            return
        import xbmcvfs
        xbmcvfs.delete(self.filepath)

    def save_meta(self):
        if not self.filepath:
            return
        import xbmcvfs
        from json import dump
        with xbmcvfs.File(self.filepath, 'w') as file:
            dump(self.meta, file, indent=4)


class ListSetFilterDir(Container):
    def get_directory(self, library='video', filename=None, filepath=None, **kwargs):
        meta_filter_dir = MetaFilterDir(library=library, filepath=filepath)

        def get_new():
            meta_filter_dir.add_new_path()
            meta_filter_dir.add_new_sort()
            meta_filter_dir.add_new_filter('filter')
            meta_filter_dir.add_new_filter('exclude')
            meta_filter_dir.write_meta(filename)
            ListGetFilterFiles(self.handle, '').get_directory()

        def do_edit():
            options = [f'path = {i}' for i in meta_filter_dir.meta['paths']]
            options += [f'{k} = {v}' for k, v in meta_filter_dir.meta.items() if k not in ('paths', 'info', 'library')]
            options += ['randomise = false'] if 'randomise' not in meta_filter_dir.meta.keys() else []
            options += ['add sort'] if 'sort_by' not in meta_filter_dir.meta.keys() else []
            options += ['add filter', 'add exclude', 'add path', 'rename', 'delete', 'save']

            x = Dialog().select(META_EDITFILTERS_HEADING, options)
            if x == -1:
                meta_filter_dir.save_meta() if Dialog().yesno(META_SAVECHANGES_HEADING, META_SAVECHANGES_MESSAGE) == 1 else None
                return

            choice_k, choice_s, choice_v = options[x].partition(' = ')

            if choice_k == 'save':
                meta_filter_dir.save_meta()
                return

            if choice_k == 'rename':
                filename = meta_filter_dir.write_meta()
                if filename:
                    import xbmc
                    meta_filter_dir.delete_meta()  # Delete the old file
                    xbmc.executebuiltin('Container.Refresh')  # Refresh container to see changes
                    return
                return do_edit()  # If user didn't enter a valid filename we just go back to menu

            if choice_k == 'delete':
                if Dialog().yesno(META_DELETEFILE_HEADING, META_DELETEFILE_MESSAGE) == 1:
                    import xbmc
                    meta_filter_dir.delete_meta()
                    xbmc.executebuiltin('Container.Refresh')
                    return
                return do_edit()

            if choice_k == 'sort_by':
                meta_filter_dir.add_new_sort_by()
                return do_edit()

            if choice_k == 'sort_how':
                meta_filter_dir.add_new_sort_how()
                return do_edit()

            if choice_k == 'path':
                meta_filter_dir.del_path(value=choice_v) if Dialog().yesno(META_DELPATH_HEADING, META_DELPATH_MESSAGE.format(choice_v)) == 1 else None
                return do_edit()

            if choice_k == 'randomise':
                meta_filter_dir.toggle_randomise()
                return do_edit()

            if choice_k == 'add path':
                meta_filter_dir.add_new_path()
                return do_edit()

            if choice_k == 'add sort':
                meta_filter_dir.add_new_sort()
                return do_edit()

            if choice_k == 'add filter':
                suffix = meta_filter_dir.get_new_suffix('filter')
                meta_filter_dir.add_new_filter('filter', suffix)
                return do_edit()

            if choice_k == 'add exclude':
                suffix = meta_filter_dir.get_new_suffix('exclude')
                meta_filter_dir.add_new_filter('exclude', suffix)
                return do_edit()

            if '_key' in choice_k:
                prefix, sep, suffix = choice_k.partition('_key')
                suffix = suffix[1:] if suffix else suffix  # Remove additional underscore on suffix
                meta_filter_dir.add_new_filter_key(prefix, suffix)
                return do_edit()

            if '_value' in choice_k:
                prefix, sep, suffix = choice_k.partition('_value')
                suffix = suffix[1:] if suffix else suffix  # Remove additional underscore on suffix
                meta_filter_dir.add_new_filter_value(prefix, suffix)
                return do_edit()

            if '_operator' in choice_k:
                prefix, sep, suffix = choice_k.partition('_operator')
                suffix = suffix[1:] if suffix else suffix  # Remove additional underscore on suffix
                meta_filter_dir.add_new_filter_operator(prefix, suffix)
                return do_edit()

            return do_edit()

        get_new() if not filepath else do_edit()


class ListGetFilterDir(Container):
    def get_directory(self, paths=None, library=None, no_label_dupes=False, dbtype=None, sort_by=None, sort_how=None, randomise=False, **kwargs):
        if not paths:
            return

        from jurialmunkey.jsnrpc import get_directory
        from jurialmunkey.parser import boolean

        update_global_property_versions()  # Add in any properties added in later JSON-RPC versions

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
            if not i:
                return

            listitem_jsonrpc = ListItemJSONRPC(i, library=library, dbtype=dbtype)
            listitem_jsonrpc.infolabels['title'] = listitem_jsonrpc.label

            for _, filters in all_filters.items():
                if is_excluded({'infolabels': listitem_jsonrpc.infolabels, 'infoproperties': listitem_jsonrpc.infoproperties}, **filters):
                    return

            if listitem_jsonrpc.mediatype:
                mediatypes[listitem_jsonrpc.mediatype] = mediatypes.get(listitem_jsonrpc.mediatype, 0) + 1

            return listitem_jsonrpc

        def _is_not_dupe(i):
            if not no_label_dupes:
                return i
            label = i.infolabels['title']
            if label in added_items:
                return
            added_items.append(label)
            return i

        def _get_sorting(i):
            v = i.infolabels.get(sort_by) or i.infoproperties.get(sort_by) or ''
            try:
                v = float(v)
                x = 2  # We want high numbers (e.g. rating/year) before empty values when sorting in descending order (reversed)
            except ValueError:
                v = str(v)
                x = 1
            except TypeError:
                v = ''
                x = 0  # We want empty values to come last when sorting in descending order (reversed)
            return (x, v)  # Sorted will sort by first value in tuple, then second order afterwards

        if boolean(randomise):
            import random
            paths = [random.choice(paths)]

        items = []
        for path in paths:
            directory = get_directory(path, directory_properties)
            with ParallelThread(directory, _make_item) as pt:
                item_queue = pt.queue
            items += [i for i in item_queue if i and (not no_label_dupes or _is_not_dupe(i))]

        items = sorted(items, key=_get_sorting, reverse=sort_how == 'desc') if sort_by else items
        items = [(i.path, i.listitem, i.is_folder, ) for i in items if i]

        plugin_category = ''
        container_content = f'{max(mediatypes, key=lambda key: mediatypes[key])}s' if mediatypes else ''
        self.add_items(items, container_content=container_content, plugin_category=plugin_category)


class ListGetContainerLabels(Container):
    def get_directory(
            self, containers, infolabel, numitems=None, thumb=None, label2=None, separator=' / ',
            filter_value=None, filter_operator=None, exclude_value=None, exclude_operator=None,
            window_prop=None, window_id=None, contextmenu=None,
            **kwargs):
        import xbmc
        from resources.lib.method import get_paramstring_tuplepairs

        filters = {
            'filter_key': 'title',
            'filter_value': filter_value,
            'filter_operator': filter_operator,
            'exclude_key': 'title',
            'exclude_value': exclude_value,
            'exclude_operator': exclude_operator,
        }

        added_items = []
        contextmenu = get_paramstring_tuplepairs(contextmenu)

        def _make_item(title, image, label):
            if (title, image, label, ) in added_items:
                return

            if is_excluded({'infolabels': {'title': title}}, **filters):
                return

            listitem = ListItem(label=title, label2=label or '', path='', offscreen=True)
            listitem.setArt({'icon': image or '', 'thumb': image or ''})
            listitem.addContextMenuItems([
                (k.format(label=title, thumb=image, label2=label), v.format(label=title, thumb=image, label2=label))
                for k, v in contextmenu])

            item = ('', listitem, True, )

            added_items.append((title, image, label, ))
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

        xbmc.executebuiltin(f'SetProperty({window_prop},{" / ".join([i[0] for i in added_items])}{f",{window_id}" if window_id else ""})')
