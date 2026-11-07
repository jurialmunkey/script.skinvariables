# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import datetime
import xbmc
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import load_filecontent, write_skinfile
from resources.lib.skinusers.actions import SkinUserAction
from resources.lib.skinusers.model import DefaultSkinUser


class SkinUserLogin(SkinUserAction):
    def __init__(self, store, slug, folder, params):
        super().__init__(store, slug)
        self.folder = folder
        self.params = params

    @property
    def template_slug(self):
        return self.get_template_slug()

    def get_template_slug(self):
        return self.slug

    @cached_property
    def content(self):
        return self.get_content()

    def get_content(self):
        content = load_filecontent('special://skin/shortcuts/skinvariables-skinusers.xmltemplate')
        return content.format(slug=self.template_slug, **self.params)

    @property
    def selection_command(self):
        return self.get_selection_command()

    def get_selection_command(self):
        return f'Skin.SetString(SkinVariables.SkinUser,{self.slug})'

    def write_xml(self):
        write_skinfile(folders=[self.folder], filename='script-skinvariables-skinusers.xml', content=self.content)

    def set_properties(self):
        last = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        executebuiltin = xbmc.getInfoLabel('Skin.String(SkinVariables.SkinUser.ExecuteBuiltIn)')
        xbmc.executebuiltin(f'Skin.SetString(SkinVariables.SkinUser.Name,{self.user.name})')
        xbmc.executebuiltin(f'Skin.SetString(SkinVariables.SkinUser.Icon,{self.user.icon})')
        xbmc.executebuiltin(self.selection_command)
        xbmc.executebuiltin(f'Skin.SetString(SkinVariables.SkinUser.{self.slug}.LastLogin,{last})')
        xbmc.executebuiltin('SetProperty(SkinVariables.SkinUserLogin,True,Home)')
        xbmc.executebuiltin(executebuiltin or 'ReloadSkin()')

    def execute(self):
        xbmc.executebuiltin('SetProperty(SkinVariables.SkinUser.LoggingIn,True,Home)')
        self.write_xml()
        self.set_properties()


class DefaultSkinUserLogin(SkinUserLogin):
    def get_user(self):
        return DefaultSkinUser()

    def get_template_slug(self):
        return ''

    def get_selection_command(self):
        return 'Skin.Reset(SkinVariables.SkinUser)'
