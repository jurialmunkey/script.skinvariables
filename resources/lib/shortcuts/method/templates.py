# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmcvfs
from json import loads
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import load_filecontent
from jurialmunkey.parser import boolean
from resources.lib.operations import RuleOperations
from resources.lib.shortcuts.futils import ADDON_DATA, FILE_PREFIX, validify_filename, write_meta_to_file
from resources.lib.shortcuts.node.tree import assign_guid


class MenuTemplate:
    def __init__(self, name, skin, template, force, params):
        self.name = name
        self.skin = skin
        self.template = template
        self.force = force
        self.parameters = params

    @cached_property
    def filename(self):
        return self.get_filename()

    def get_filename(self):
        return validify_filename(f'{FILE_PREFIX}{self.name}.json')

    @cached_property
    def filepath(self):
        return self.get_filepath()

    def get_filepath(self):
        return f'{ADDON_DATA}{self.skin}/{self.filename}'

    @cached_property
    def meta(self):
        return self.get_meta()

    def get_meta(self):
        return loads(str(load_filecontent(self.template)))

    @cached_property
    def params(self):
        return self.get_params()

    def get_params(self):
        return RuleOperations(self.meta, **self.parameters).params

    def format(self, value):
        if isinstance(value, str):
            return value.format_map(self.params)
        if isinstance(value, list):
            return [self.format(item) for item in value]
        if isinstance(value, dict):
            return {key: self.format(item) for key, item in value.items()}
        return value

    @cached_property
    def menu(self):
        return self.get_menu()

    def get_menu(self):
        params = self.params
        return self.format(self.meta.get('menu') or [])

    def write(self):
        if not boolean(self.force) and xbmcvfs.exists(self.filepath):
            return
        write_meta_to_file(
            assign_guid(self.menu),
            folder=self.skin,
            filename=self.filename,
            fileprop=f'{self.skin}-{self.filename}',
            reload=True,
        )
