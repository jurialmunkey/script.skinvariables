# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import xbmcvfs
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import check_hash, make_hash, write_skinfile, write_file, load_filecontent
from resources.lib.viewtypes.common import ADDON_DATA
from resources.lib.xmlhelper.serializer import make_xml_includes
from resources.lib.xmlhelper.skin import get_skinfolders


class ViewTypesStorage:
    filename = 'script-skinviewtypes-includes.xml'

    def __init__(self):
        if not xbmcvfs.exists(ADDON_DATA):
            xbmcvfs.mkdir(ADDON_DATA)

    def read_template(self):
        return load_filecontent('special://skin/shortcuts/skinviewtypes.json')

    @cached_property
    def addon_datafile(self):
        return self.get_addon_datafile()

    def get_addon_datafile(self):
        return f'{ADDON_DATA}{xbmc.getSkinDir()}-viewtypes.json'

    @cached_property
    def skinfolders(self):
        return self.get_skinfolders()

    def get_skinfolders(self):
        return get_skinfolders()

    def read_preferences(self, filepath):
        return load_filecontent(filepath)

    def save_preferences(self, filepath, content):
        write_file(filepath=filepath, content=content)

    def write_xml(self, folders, xmltree, hashvalue):
        write_skinfile(
            folders=folders,
            filename=self.filename,
            content=make_xml_includes(xmltree),
            checksum='script-skinviewtypes-checksum',
            hashname='script-skinviewtypes-hash',
            hashvalue=hashvalue,
        )

    def xmlfile_exists(self, folders, hashname):
        for folder in folders:
            filepath = f'special://skin/{folder}/{self.filename}'
            if not xbmcvfs.exists(filepath):
                return False
            content = load_filecontent(filepath)
            if content and check_hash(hashname, make_hash(content)):
                return False
        return True
