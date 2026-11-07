# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import jurialmunkey.futils


ADDONDATA = 'special://profile/addon_data/script.skinvariables/'
TAB = '    '
DATA_FOLDER = 'special://profile/addon_data/script.skinshortcuts/'
SKIN_FOLDER = 'special://skin/shortcuts/'


class FileUtils(jurialmunkey.futils.FileUtils):
    addondata = ADDONDATA   # Override module addon_data with plugin addon_data


FILEUTILS = FileUtils()
delete_file = FILEUTILS.delete_file
