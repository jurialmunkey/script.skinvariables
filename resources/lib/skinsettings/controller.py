# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import xbmcvfs
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import write_file
from resources.lib.skinsettings.definition import SkinSettingsDefinition
from resources.lib.skinsettings.template import get_skinsettings_template
from resources.lib.skinsettings.window import SkinSettingsWindow
from resources.lib.xmlhelper.skin import get_skinfolders


# Kodi looks for script windows missing from the skin in {scriptpath}/resources/skins/{skin id}/{skin folder}/
SKINSETTINGS_FOLDER = 'special://profile/addon_data/script.skinvariables/skinsettings/'
WINDOW_FILENAME = 'script-skinvariables-skinsettings-generated.xml'


class SkinSettingsWindowFile:
    def __init__(self, folder, definition):
        self.folder = folder
        self.definition = definition

    @cached_property
    def template(self):
        return get_skinsettings_template(self.folder, self.definition)

    @cached_property
    def folderpath(self):
        return f'{SKINSETTINGS_FOLDER}resources/skins/{xbmc.getSkinDir()}/{self.folder}/'

    @cached_property
    def filepath(self):
        return f'{self.folderpath}{WINDOW_FILENAME}'

    def write(self):
        xbmcvfs.mkdirs(self.folderpath)
        write_file(filepath=self.filepath, content=self.template.text)


class SkinSettingsController:
    def __init__(self, filepath):
        self.filepath = filepath

    @cached_property
    def definition(self):
        return SkinSettingsDefinition(self.filepath)

    @cached_property
    def folders(self):
        return tuple(dict.fromkeys(get_skinfolders()))

    @cached_property
    def window_files(self):
        return [SkinSettingsWindowFile(folder, self.definition) for folder in self.folders]

    def write(self):
        for window_file in self.window_files:
            window_file.write()

    def run(self):
        self.write()
        scriptpath = xbmcvfs.translatePath(SKINSETTINGS_FOLDER)
        window = SkinSettingsWindow(WINDOW_FILENAME, scriptpath, 'Default', '1080i', definition=self.definition)
        window.doModal()
        del window


def run_skinsettings(run_skinsettings, **kwargs):
    SkinSettingsController(run_skinsettings).run()
