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
        meta = read_meta_from_file(self.filepath) or self.get_blank_meta()
        names = meta.setdefault('names', [])
        names.extend([''] * (len(meta['paths']) - len(names)))
        return meta

    @property
    def paths(self):
        return self.meta['paths']

    @property
    def names(self):
        return self.meta['names']

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
        index = Dialog().select(heading, methods)
        if index == -1:
            return None
        method = methods[index]
        if method == 'custom':
            return Dialog().input(heading=customheading)
        if method == 'none':
            return ''
        return method

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

    def del_path(self, index):
        del self.paths[index]
        del self.names[index]

    def rename_path(self, index):
        name = Dialog().input(heading=get_localized(551), defaultt=self.names[index])
        if not name:
            return
        self.names[index] = name

    def add_new_path(self):
        while True:
            path, name = self.get_new_path()
            if path is None:
                break
            name = Dialog().input(heading=get_localized(551), defaultt=name)
            self.paths.append(path)
            self.names.append(name)
            if not Dialog().yesno(get_localized(32030), get_localized(32031)):
                break
        return self.paths

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
        choices = [get_localized(label) for _, label in STANDARD_OPERATORS]
        index = Dialog().select(f'[CAPITALIZE]{prefix}[/CAPITALIZE] operator', choices)
        if index == -1:
            return
        filter_operator = STANDARD_OPERATORS[index][0]
        key = self.get_filter_key(prefix, 'operator', suffix)
        self.meta[key] = filter_operator
        return filter_operator

    def add_new_filter_key(self, prefix='filter', suffix=''):
        filter_key = self.get_new_method(get_localized(32032).format(prefix), get_localized(32034).format(prefix))
        if filter_key is None:
            return
        if filter_key == '':
            self.del_filter(prefix, suffix)
            return
        key = self.get_filter_key(prefix, 'key', suffix)
        self.meta[key] = filter_key
        return filter_key

    def add_new_filter_value(self, prefix='filter', suffix=''):
        key = self.get_filter_key(prefix, 'key', suffix)
        if not self.meta.get(key):
            self.del_filter(prefix, suffix)
            return
        filter_value = Dialog().input(heading=get_localized(32035).format(prefix))
        if not filter_value:
            self.del_filter(prefix, suffix)
            return
        key = self.get_filter_key(prefix, 'value', suffix)
        self.meta[key] = filter_value
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


class FilterDirOption:
    def __init__(self, label):
        self.label = label

    def select(self):
        return False


class FilterDirAction(FilterDirOption):
    close_after_action = False

    def __init__(self, label, action, *args):
        super().__init__(label)
        self.action = action
        self.args = args

    def select(self):
        result = self.action(*self.args)
        return self.close_after_action and result is not False


class ClosingFilterDirAction(FilterDirAction):
    close_after_action = True


class FilterDirEditor:
    def __init__(self, library='video', filepath=None):
        self.metadata = MetaFilterDir(library=library, filepath=filepath)

    @property
    def options(self):
        return self.get_options()

    def get_options(self):
        return self.path_options + self.metadata_options + self.action_options

    @property
    def path_options(self):
        return self.get_path_options()

    def get_path_options(self):
        return [option for index in range(len(self.metadata.paths)) for option in self.get_path_pair_options(index)]

    def get_path_pair_options(self, index):
        return [
            FilterDirAction(f'path = {self.metadata.paths[index]}', self.delete_path, index),
            FilterDirAction(f'name = {self.metadata.names[index]}', self.metadata.rename_path, index),
        ]

    @property
    def metadata_options(self):
        return self.get_metadata_options()

    def get_metadata_options(self):
        options = [
            self.get_metadata_option(key, value)
            for key, value in self.metadata.meta.items()
            if key not in ('paths', 'info', 'library', 'names')
        ]
        options.extend(
            self.get_metadata_option(key, 'false')
            for key in ('randomise', 'fallback')
            if key not in self.metadata.meta
        )
        return options

    @cached_property
    def actions(self):
        return self.get_actions()

    def get_actions(self):
        return {
            'sort_by': self.metadata.add_new_sort_by,
            'sort_how': self.metadata.add_new_sort_how,
            'randomise': self.metadata.toggle_randomise,
            'fallback': self.metadata.toggle_fallback,
        }

    @cached_property
    def filter_actions(self):
        return self.get_filter_actions()

    def get_filter_actions(self):
        return {
            'key': self.metadata.add_new_filter_key,
            'value': self.metadata.add_new_filter_value,
            'operator': self.metadata.add_new_filter_operator,
        }

    def get_metadata_option(self, key, value):
        label = f'{key} = {value}'
        if key in self.actions:
            return FilterDirAction(label, self.actions[key])
        for field, action in self.filter_actions.items():
            prefix, separator, suffix = key.partition(f'_{field}')
            if separator:
                return FilterDirAction(label, action, prefix, suffix[1:])
        return FilterDirOption(label)

    @property
    def action_options(self):
        return self.get_action_options()

    def get_action_options(self):
        options = []
        if 'sort_by' not in self.metadata.meta:
            options.append(FilterDirAction('add sort', self.metadata.add_new_sort))
        return options + [
            FilterDirAction('add filter', self.add_filter, 'filter'),
            FilterDirAction('add exclude', self.add_filter, 'exclude'),
            FilterDirAction('add path', self.metadata.add_new_path),
            ClosingFilterDirAction('rename', self.rename_meta),
            ClosingFilterDirAction('delete', self.delete_meta),
            ClosingFilterDirAction('save', self.metadata.save_meta),
        ]

    def create(self, filename=None):
        self.metadata.add_new_path()
        self.metadata.add_new_sort()
        self.metadata.add_new_filter('filter')
        self.metadata.add_new_filter('exclude')
        return self.metadata.write_meta(filename)

    def edit(self):
        while True:
            options = self.options
            index = Dialog().select(get_localized(21435), [option.label for option in options])
            if index == -1:
                if Dialog().yesno(get_localized(32044), get_localized(32045)):
                    self.metadata.save_meta()
                return
            if options[index].select():
                return

    def add_filter(self, prefix):
        self.metadata.add_new_filter(prefix, self.metadata.get_new_suffix(prefix))

    def delete_path(self, index):
        path = self.metadata.paths[index]
        if Dialog().yesno(get_localized(32042), '\n'.join((path, get_localized(32043)))):
            self.metadata.del_path(index)

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
