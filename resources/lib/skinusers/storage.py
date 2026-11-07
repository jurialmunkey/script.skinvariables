# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from json import loads
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import FileUtils as BaseFileUtils, load_filecontent
from resources.lib.skinusers.model import SkinUser


BASEFOLDER = 'special://profile/addon_data/script.skinvariables/logins/'
USERS_FILE = 'skinusers.json'


class FileUtils(BaseFileUtils):
    addondata = BASEFOLDER


class SkinUserStore:
    def __init__(self, skinid):
        self.skinid = skinid
        self.meta = self.get_meta()

    @cached_property
    def filepath(self):
        return self.get_filepath()

    def get_filepath(self):
        return f'{BASEFOLDER}/{self.skinid}/{USERS_FILE}'

    def get_meta(self):
        content = load_filecontent(self.filepath)
        return loads(content) if content else []

    @property
    def users(self):
        return self.get_users()

    def get_users(self):
        return [SkinUser(meta) for meta in self.meta]

    def get_user(self, slug):
        return SkinUser(next(meta for meta in self.meta if slug == meta.get('slug')))

    def save(self):
        FileUtils().dumps_to_file(self.meta, folder=self.skinid, filename=USERS_FILE, indent=4)
