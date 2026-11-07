# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import xbmcaddon
from json import loads
from jurialmunkey.logger import TimerFunc
from jurialmunkey.ftools import cached_property
from jurialmunkey.parser import boolean
from jurialmunkey.futils import load_filecontent, write_skinfile
from resources.lib.kodiutils import ProgressDialog, get_localized
from resources.lib.shortcuts.profile import PROFILE_SETTING, ProfileIncludes
from resources.lib.shortcuts.template.common import SKIN_BASEDIR, SHORTCUTS_FOLDER
from resources.lib.shortcuts.template.document import TemplateDocument
from resources.lib.shortcuts.template.build import TemplateBuild

ADDON = xbmcaddon.Addon()


class ShortcutsTemplate(object):
    allow_users = True

    def __init__(self, template: str = None):
        self.template = f'skinvariables-generator-{template}' if template else 'skinvariables-generator'
        self.hashname = f'script-{self.template}{self.skinuser}-hash'
        self.contents = load_filecontent(f'{SKIN_BASEDIR}/{SHORTCUTS_FOLDER}/{self.template}.json')
        self.meta = loads(self.contents) or {}
        self.folder = self.meta.get('folder') or SHORTCUTS_FOLDER
        self.profilename = xbmc.getInfoLabel('System.ProfileName')
        self.p_dialog = None

    @cached_property
    def output(self):
        return self.get_output()

    def get_output(self):
        filename = self.meta['output'].format(skinuser=self.skinuser)
        return ProfileIncludes(self.folder, filename, self.profilename)

    @cached_property
    def skinuser(self):
        return self.get_skinuser()

    def get_skinuser(self):
        return '' if not self.allow_users else xbmc.getInfoLabel('Skin.String(SkinVariables.SkinUser)') or ''

    @cached_property
    def filepath(self):
        return self.get_filepath()

    def get_filepath(self):
        return self.output.filepath

    @cached_property
    def filename(self):
        return self.get_filename()

    def get_filename(self):
        return self.output.profile_filename

    @cached_property
    def skinid(self):
        return self.get_skinid()

    def get_skinid(self):
        self._skinid = self.meta.get('skinid')
        if not self._skinid or not self.skinuser:
            return self._skinid
        return f'{self._skinid}-{self.skinuser}'

    def create_xml(self):
        return TemplateDocument(self).content

    def update_xml(self, force=False, no_reload=False, genxml='', background=True, **kwargs):
        if not self.meta:
            return

        build = TemplateBuild(self, genxml, kwargs, force)

        profile_changed = xbmc.getInfoLabel(f'Skin.String({PROFILE_SETTING})') != self.output.profilehash
        if profile_changed:
            xbmc.executebuiltin(f'Skin.SetString({PROFILE_SETTING},{self.output.profilehash})')

        if build.updated:
            dispatcher_changed = self.output.update_dispatcher()
            if not no_reload and (dispatcher_changed or profile_changed):
                xbmc.executebuiltin('ReloadSkin()')
            return

        with TimerFunc('script.skinvariables - update_xml: ', log_threshold=0.001, inline=True):
            with ProgressDialog(
                ADDON.getLocalizedString(32001),
                f'{get_localized(32049)}...',
                logging=2,
                total=4,
                background=boolean(background),
            ) as self.p_dialog:
                build.prepare()
                content = self.create_xml()
                write_skinfile(folders=[self.folder], filename=self.filename, content=content)
                if load_filecontent(self.filepath) != content:
                    raise OSError(f'Failed to write generated includes: {self.filepath}')
                self.output.update_dispatcher()
                xbmc.executebuiltin('Skin.SetString({},{})'.format(self.hashname, build.current_hash))

        if no_reload:
            return

        xbmc.Monitor().waitForAbort(0.5)
        xbmc.executebuiltin('ReloadSkin()')
