# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from xbmcgui import Dialog, INPUT_NUMERIC
from jurialmunkey.ftools import cached_property
from resources.lib.kodiutils import get_localized
from resources.lib.shortcuts.futils import reload_shortcut_dir
from resources.lib.skinusers.model import NewSkinUser


class SkinUserAction:
    """Authenticate a selected user before running a protected action."""

    def __init__(self, store, slug):
        self.store = store
        self.slug = slug

    @cached_property
    def user(self):
        return self.get_user()

    def get_user(self):
        return self.store.get_user(self.slug)

    def authenticate(self):
        if not self.user.code:
            return True
        code = Dialog().input(get_localized(32057), type=INPUT_NUMERIC)
        if str(self.user.code) == str(code):
            return True
        Dialog().ok(get_localized(32063), get_localized(32060))
        return False

    def run(self):
        if self.authenticate():
            self.execute()

    def execute(self):
        raise NotImplementedError


class RenameSkinUser(SkinUserAction):
    def execute(self):
        name = Dialog().input(get_localized(32066), defaultt=self.user.meta.get('name', ''))
        if not name:
            return
        self.user.meta['name'] = name
        self.store.save()
        reload_shortcut_dir()


class DeleteSkinUser(SkinUserAction):
    def execute(self):
        message = f'{get_localized(32065).format(self.user.meta["name"])}\n{get_localized(32043)}'
        if not Dialog().yesno(get_localized(32064), message):
            return
        self.store.meta.remove(self.user.meta)
        self.store.save()
        reload_shortcut_dir()


class ToggleDefaultSkinUser:
    def run(self):
        xbmc.executebuiltin('Skin.ToggleSetting(SkinVariables.SkinUsers.DisableDefaultUser)')
        reload_shortcut_dir()


class AddSkinUser:
    def __init__(self, store):
        self.store = store

    def get_code(self):
        while Dialog().yesno(get_localized(32055), get_localized(32056)):
            code = Dialog().input(get_localized(32057), type=INPUT_NUMERIC)
            if not code:
                return
            if Dialog().input(get_localized(32058), type=INPUT_NUMERIC) == code:
                return str(code)

    def run(self):
        name = Dialog().input(get_localized(32054))
        if not name:
            return
        user = NewSkinUser(name, self.get_code())
        self.store.meta.append(user.meta)
        self.store.save()
        reload_shortcut_dir()
