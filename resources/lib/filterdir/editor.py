# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import Dialog
from jurialmunkey.ftools import cached_property
from jurialmunkey.window import WindowProperty
from resources.lib.kodiutils import get_localized


SORTBY_METHODS = [
    'none',
    'title',
    'genre',
    'year',
    'rating',
    'playcount',
    'director',
    'trailer',
    'tagline',
    'plot',
    'originaltitle',
    'lastplayed',
    'writer',
    'studio',
    'mpaa',
    'country',
    'premiered',
    'top250',
    'votes',
    'tvshowtitle',
    'custom',
]

STANDARD_OPERATORS = (
    ('contains', 21400),
    ('lt', 32036),
    ('le', 32037),
    ('eq', 32038),
    ('ne', 32039),
    ('ge', 32040),
    ('gt', 32041),
)


class MetaFilterDir:
    def __init__(self, library='video', filepath=None):
        self.library = library
        self.filepath = filepath

    @cached_property
    def meta(self):
        return self.get_files_meta()

    def get_blank_meta(self):
        return {'info': 'get_filter_dir', 'library': self.library, 'paths': [], 'names': []}

    def get_files_meta(self):
        if not self.filepath:
            return self.get_blank_meta()
        from resources.lib.shortcuts.futils import read_meta_from_file
        return read_meta_from_file(self.filepath) or self.get_blank_meta()

    @staticmethod
    def get_new_path():
        from resources.lib.shortcuts.browser import GetDirectoryBrowser
        with WindowProperty(('IsSkinShortcut', 'True')):
            directory_browser = GetDirectoryBrowser(use_rawpath=True)
            item = directory_browser.get_directory(path='library://video/')  # TODO: Add some choice of library
            name = directory_browser.heading_str
        try:
            path = item['path']
        except (TypeError, KeyError):
            return (None, None)
        return (path, name)

    @staticmethod
    def get_new_method(heading, customheading, methods=SORTBY_METHODS):
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
        key_prefix = f'{prefix}_key__'
        existing_suffixes = {key[len(key_prefix):] for key in self.meta if key.startswith(key_prefix)}
        while True:
            suffix = f'{random.randrange(16**8):08x}'
            if suffix not in existing_suffixes:
                return f'_{suffix}'  # Joining the key adds the second underscore.

    @staticmethod
    def get_filter_key(prefix, key, suffix=''):
        return '_'.join(part for part in (prefix, key, suffix) if part)

    def toggle_option(self, key):
        from jurialmunkey.parser import boolean
        if boolean(self.meta.get(key, False)):
            del self.meta[key]
            return
        self.meta[key] = 'true'

    def toggle_randomise(self):
        self.toggle_option('randomise')

    def toggle_fallback(self):
        self.toggle_option('fallback')

    def del_path(self, value):
        x = self.meta['paths'].index(value)
        del self.meta['paths'][x]
        del self.meta['names'][x]

    def rename_path(self, x):
        name = Dialog().input(heading=get_localized(551), defaultt=self.meta['names'][x])
        if not name:
            return
        self.meta['names'][x] = name

    def add_new_path(self):
        while True:
            path, name = self.get_new_path()
            if path is None:
                break
            name = Dialog().input(heading=get_localized(551), defaultt=name)
            self.meta['paths'].append(path)
            self.meta['names'].append(name)
            if not Dialog().yesno(get_localized(32030), get_localized(32031)):
                break
        return self.meta['paths']

    def add_new_sort_how(self):
        self.meta['sort_how'] = 'desc' if Dialog().yesno(
            get_localized(580),  # Sort direction
            '',
            yeslabel=get_localized(585),  # Descending
            nolabel=get_localized(584),  # Ascending
        ) else 'asc'

    def add_new_sort_by(self):
        sort_by = self.get_new_method(
            get_localized(32032).format(get_localized(32033)),
            get_localized(32034).format(get_localized(32033)),
        )
        if sort_by is None:
            return
        self.meta['sort_by'] = sort_by

    def add_new_sort(self):
        self.add_new_sort_by()
        if not self.meta.get('sort_by'):
            return
        self.add_new_sort_how()

    def del_filter(self, prefix='filter', suffix='', keys=('key', 'value', 'operator')):
        for key in keys:
            self.meta.pop(self.get_filter_key(prefix, key, suffix), None)

    def add_new_filter_operator(self, prefix='filter', suffix=''):
        choices = [(k, get_localized(v)) for k, v in STANDARD_OPERATORS]
        x = Dialog().select('[CAPITALIZE]{}[/CAPITALIZE] operator'.format(prefix), [i for _, i in choices])
        if x == -1:
            return
        filter_operator = choices[x][0]
        k = self.get_filter_key(prefix, 'operator', suffix)
        self.meta[k] = filter_operator
        return filter_operator

    def add_new_filter_key(self, prefix='filter', suffix=''):
        filter_key = self.get_new_method(get_localized(32032).format(prefix), get_localized(32034).format(prefix))
        if filter_key is None:
            return
        if filter_key == '':
            self.del_filter(prefix, suffix)
            return
        k = self.get_filter_key(prefix, 'key', suffix)
        self.meta[k] = filter_key
        return filter_key

    def add_new_filter_value(self, prefix='filter', suffix=''):
        k = self.get_filter_key(prefix, 'key', suffix)
        if not self.meta.get(k):
            self.del_filter(prefix, suffix)
            return
        filter_value = Dialog().input(heading=get_localized(32035).format(prefix))
        if not filter_value:
            self.del_filter(prefix, suffix)
            return
        k = self.get_filter_key(prefix, 'value', suffix)
        self.meta[k] = filter_value
        return filter_value

    def add_new_filter(self, prefix='filter', suffix=''):
        if not self.add_new_filter_key(prefix, suffix):
            return
        self.add_new_filter_operator(prefix, suffix)
        self.add_new_filter_value(prefix, suffix)

    def write_meta(self, filename=None):
        from resources.lib.shortcuts.futils import FILEUTILS, validify_filename
        filename = filename or Dialog().input(heading=get_localized(551))
        filename = validify_filename(filename)
        if not filename:  # TODO: Ask user if they are sure they dont want to make the file.
            return
        filename = f'{filename}.json'
        # TODO: Make sure we don't overwrite an existing file.
        FILEUTILS.dumps_to_file(self.meta, folder='dynamic', filename=filename, indent=4)
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


class FilterDirEditor:
    def __init__(self, library='video', filepath=None):
        self.metadata = MetaFilterDir(library=library, filepath=filepath)

    @property
    def options(self):
        return self.get_options()

    def get_options(self):
        meta = self.metadata.meta
        names = meta.setdefault('names', [])
        names.extend([''] * (len(meta['paths']) - len(names)))
        options = [
            option
            for index, path in enumerate(meta['paths'])
            for option in (f'path = {path}', f'name = {names[index]}')
        ]
        options.extend(
            f'{key} = {value}'
            for key, value in meta.items()
            if key not in ('paths', 'info', 'library', 'names')
        )
        options.extend(f'{key} = false' for key in ('randomise', 'fallback') if key not in meta)
        if 'sort_by' not in meta:
            options.append('add sort')
        options.extend(('add filter', 'add exclude', 'add path', 'rename', 'delete', 'save'))
        return options

    def create(self, filename=None):
        self.metadata.add_new_path()
        self.metadata.add_new_sort()
        self.metadata.add_new_filter('filter')
        self.metadata.add_new_filter('exclude')
        return self.metadata.write_meta(filename)

    def edit(self):
        while True:
            options = self.options
            index = Dialog().select(get_localized(21435), options)
            if index == -1:
                if Dialog().yesno(get_localized(32044), get_localized(32045)):
                    self.metadata.save_meta()
                return
            if self.edit_option(options[index], index):
                return

    @cached_property
    def actions(self):
        return self.get_actions()

    def get_actions(self):
        return {
            'sort_by': self.metadata.add_new_sort_by,
            'sort_how': self.metadata.add_new_sort_how,
            'randomise': self.metadata.toggle_randomise,
            'fallback': self.metadata.toggle_fallback,
            'add path': self.metadata.add_new_path,
            'add sort': self.metadata.add_new_sort,
        }

    def edit_option(self, option, index):
        key, _, value = option.partition(' = ')
        if key == 'save':
            self.metadata.save_meta()
            return True
        if key == 'rename':
            return self.rename_meta()
        if key == 'delete':
            return self.delete_meta()
        if key == 'path':
            if Dialog().yesno(get_localized(32042), '\n'.join((value, get_localized(32043)))):
                self.metadata.del_path(value)
            return
        if key == 'name':
            self.metadata.rename_path((index - 1) // 2)
            return
        if key in self.actions:
            self.actions[key]()
            return
        if key in ('add filter', 'add exclude'):
            prefix = key.split()[1]
            self.metadata.add_new_filter(prefix, self.metadata.get_new_suffix(prefix))
            return
        self.edit_filter(key)

    def edit_filter(self, key):
        for field in ('key', 'value', 'operator'):
            prefix, separator, suffix = key.partition(f'_{field}')
            if separator:
                method = getattr(self.metadata, f'add_new_filter_{field}')
                method(prefix, suffix[1:] if suffix else '')
                return

    @staticmethod
    def refresh_container():
        import xbmc
        xbmc.executebuiltin('Container.Refresh')

    def rename_meta(self):
        if not self.metadata.write_meta():
            return False
        self.metadata.delete_meta()
        self.refresh_container()
        return True

    def delete_meta(self):
        if not Dialog().yesno(get_localized(117), get_localized(32043)):
            return False
        self.metadata.delete_meta()
        self.refresh_container()
        return True
