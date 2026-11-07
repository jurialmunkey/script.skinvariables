# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from xbmcgui import ListItem
from jurialmunkey.ftools import cached_property
from jurialmunkey.parser import boolean
from resources.lib.kodiutils import get_localized
from resources.lib.skinusers.model import DefaultSkinUser


BASEPLUGIN = 'plugin://script.skinvariables/'


class SkinUserMenu:
    def __init__(self, skinid, folder):
        self.skinid = skinid
        self.folder = folder

    def get_path(self, info, slug=None):
        path = f'{BASEPLUGIN}?info={info}&skinid={self.skinid}'
        if slug is not None:
            path += f'&slug={slug}'
        return f'{path}&folder={self.folder}' if self.folder else path

    @property
    def show_default(self):
        return self.get_show_default()

    def get_show_default(self):
        return xbmc.getCondVisibility('!Skin.HasSetting(SkinVariables.SkinUsers.DisableDefaultUser)')

    @property
    def toggle_item(self):
        return self.get_toggle_item()

    def get_toggle_item(self):
        path = self.get_path('get_skin_user', 'default')
        disabled = xbmc.getCondVisibility('Skin.HasSetting(SkinVariables.SkinUsers.DisableDefaultUser)')
        return (get_localized(32097 if disabled else 32098), f'RunPlugin({path}&func=toggle)')


class SkinUserItem:
    def __init__(self, user, menu):
        self.user = user
        self.menu = menu

    @cached_property
    def path(self):
        return self.get_path()

    def get_path(self):
        return self.menu.get_path('get_skin_user', self.user.slug or '')

    @property
    def last_login(self):
        return self.get_last_login()

    def get_last_login(self):
        last = xbmc.getInfoLabel(f'Skin.String(SkinVariables.SkinUser.{self.user.slug or ""}.LastLogin)')
        return last or get_localized(32062)

    def get_actions(self):
        return [('Rename', f'RunPlugin({self.path}&func=rename)'), ('Delete', f'RunPlugin({self.path}&func=delete)')]

    @property
    def contextmenu(self):
        return self.get_contextmenu()

    def get_contextmenu(self):
        return self.get_actions() if self.user.has_menu else []

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        if not self.user.name:
            return
        last = self.last_login
        item = ListItem(label=self.user.name, label2=last, path=self.path)
        item.setProperty('last', last)
        item.setProperty('slug', self.user.slug or '')
        if self.user.code:
            item.setProperty('code', self.user.code)
        if self.user.icon:
            item.setArt({'thumb': self.user.icon, 'icon': self.user.icon})
        item.addContextMenuItems(self.contextmenu)
        return (self.path, item, False)


class DefaultSkinUserItem(SkinUserItem):
    def get_actions(self):
        return [self.menu.toggle_item]


class SkinUserDirectory:
    def __init__(self, store, folder, allow_new=False):
        self.store = store
        self.menu = SkinUserMenu(store.skinid, folder)
        self.allow_new = boolean(allow_new)

    def get_user_item(self, user):
        item_class = DefaultSkinUserItem if user.slug == 'default' else SkinUserItem
        return item_class(user, self.menu).result

    @property
    def user_items(self):
        return self.get_user_items()

    def get_user_items(self):
        items = (self.get_user_item(user) for user in self.store.users)
        return [item for item in items if item is not None]

    @property
    def default_items(self):
        return self.get_default_items()

    def get_default_items(self):
        if not self.menu.show_default:
            return []
        return [DefaultSkinUserItem(DefaultSkinUser(), self.menu).result]

    @property
    def add_items(self):
        return self.get_add_items()

    def get_add_items(self):
        if not self.allow_new:
            return []
        path = self.menu.get_path('add_skin_user')
        item = ListItem(label=f'{get_localized(32096)}...', path=path)
        item.addContextMenuItems([self.menu.toggle_item])
        return [(path, item, False)]

    @property
    def items(self):
        return self.get_items()

    def get_items(self):
        return self.default_items + self.user_items + self.add_items
