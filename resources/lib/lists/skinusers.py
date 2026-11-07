# -*- coding: utf-8 -*-
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.litems import ContainerDirectory
from resources.lib.skinusers.actions import AddSkinUser, DeleteSkinUser, RenameSkinUser, ToggleDefaultSkinUser
from resources.lib.skinusers.items import SkinUserDirectory
from resources.lib.skinusers.login import SkinUserLogin, DefaultSkinUserLogin
from resources.lib.skinusers.storage import SkinUserStore


class ListAddSkinUser(ContainerDirectory):
    def get_directory(self, skinid, **kwargs):
        AddSkinUser(SkinUserStore(skinid)).run()


class ListGetSkinUser(ContainerDirectory):
    def get_action(self, store, slug, folder, func, params):
        if func == 'toggle':
            return ToggleDefaultSkinUser()
        actions = {'delete': DeleteSkinUser, 'rename': RenameSkinUser}
        if func in actions:
            return actions[func](store, slug)
        login_class = DefaultSkinUserLogin if slug == 'default' else SkinUserLogin
        return login_class(store, slug, folder, params)

    def get_directory(self, skinid, folder, slug=None, allow_new=False, func=None, **kwargs):
        store = SkinUserStore(skinid)
        if not slug:
            items = SkinUserDirectory(store, folder, allow_new).items
            self.add_items(items, container_content='', plugin_category='')
            return
        self.get_action(store, slug, folder, func, kwargs).run()
