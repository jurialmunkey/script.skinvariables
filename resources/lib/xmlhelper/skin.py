# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xml.etree.ElementTree as ET
import xbmcvfs
from jurialmunkey.ftools import cached_property


class SkinFolders:
    def __init__(self, filepath='special://skin/addon.xml'):
        self.filepath = filepath

    @cached_property
    def content(self):
        return self.get_content()

    def get_content(self):
        with xbmcvfs.File(self.filepath) as addonfile:
            return addonfile.read()

    @cached_property
    def root(self):
        return self.get_root()

    def get_root(self):
        return ET.fromstring(self.content)

    @cached_property
    def extensions(self):
        return self.get_extensions()

    def get_extensions(self):
        return [child for child in self.root if child.attrib.get('point') == 'xbmc.gui.skin']

    @cached_property
    def folders(self):
        return self.get_folders()

    def get_folders(self):
        return [
            resolution.attrib['folder']
            for extension in self.extensions
            for resolution in extension
            if resolution.tag == 'res' and resolution.attrib.get('folder')
        ]


def get_skinfolders():
    return SkinFolders().folders
