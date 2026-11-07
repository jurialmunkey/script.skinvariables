# -*- coding: utf-8 -*-
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import xbmcgui
import xbmcaddon
from json import loads
from jurialmunkey.futils import load_filecontent, write_skinfile, make_hash
from resources.lib.variables.generator import VariablesBuilder
from resources.lib.variables.xml import XMLVariables
from resources.lib.xmlhelper.serializer import make_xml_includes
from resources.lib.xmlhelper.skin import get_skinfolders


ADDON = xbmcaddon.Addon()


class SkinVariables:
    def __init__(self, template: str = None, skinfolder: str = None):
        self.template = f'skinvariables-{template}' if template else 'skinvariables'
        self.filename = f'script-{self.template}-includes.xml'
        self.hashname = f'script-{self.template}-hash'
        self.folders = [skinfolder] if skinfolder else get_skinfolders()
        self.content = self.get_content()
        self.meta = loads(self.content) or []

    def get_content(self):
        filepath = f'special://skin/shortcuts/{self.template}'
        xmlstring = load_filecontent(f'{filepath}.xml')
        if xmlstring:
            return XMLVariables(xmlstring).content
        return load_filecontent(f'{filepath}.json')

    @property
    def xmltree(self):
        return self.get_xmltree()

    def get_xmltree(self):
        return VariablesBuilder(self.meta).xmltree

    def is_updated(self, hashvalue):
        last_version = xbmc.getInfoLabel(f'Skin.String({self.hashname})')
        return bool(hashvalue and last_version and hashvalue == last_version)

    def write_xml(self, p_dialog, hashvalue):
        xmltree = self.xmltree
        if not self.folders:
            return
        write_skinfile(
            folders=self.folders,
            filename=self.filename,
            content=make_xml_includes(xmltree, p_dialog=p_dialog),
            hashvalue=hashvalue,
            hashname=self.hashname,
        )

    def update_xml(self, force=False, no_reload=False, **kwargs):
        if not self.meta:
            return
        hashvalue = make_hash(self.content)
        if not force and self.is_updated(hashvalue):
            return

        p_dialog = xbmcgui.DialogProgressBG()
        p_dialog.create(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32000))
        try:
            self.write_xml(p_dialog, hashvalue)
        finally:
            p_dialog.close()
        if not no_reload:
            xbmc.executebuiltin('ReloadSkin()')
