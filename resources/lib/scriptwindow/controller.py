# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import xbmcvfs
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import write_file
from resources.lib.xmlhelper.skin import get_skinfolders


class ScriptWindowFile:
    """Generated window file for one skin folder.

    Kodi looks for script windows missing from the skin in {scriptpath}/resources/skins/{skin id}/{skin folder}/
    """

    basefolder = ''
    filename = ''

    def __init__(self, folder):
        self.folder = folder

    @cached_property
    def template(self):
        return self.get_template()

    def get_template(self):
        raise NotImplementedError

    @cached_property
    def folderpath(self):
        return f'{self.basefolder}resources/skins/{xbmc.getSkinDir()}/{self.folder}/'

    @cached_property
    def filepath(self):
        return f'{self.folderpath}{self.filename}'

    def write(self):
        xbmcvfs.mkdirs(self.folderpath)
        write_file(filepath=self.filepath, content=self.template.text)


class ScriptWindowController:
    """Writes the generated window file for each skin folder and shows the window."""

    window_file_class = ScriptWindowFile
    window_class = None

    @cached_property
    def folders(self):
        return self.get_folders()

    def get_folders(self):
        return tuple(dict.fromkeys(get_skinfolders()))

    @cached_property
    def window_files(self):
        return self.get_window_files()

    def get_window_files(self):
        return [self.get_window_file(folder) for folder in self.folders]

    def get_window_file(self, folder):
        raise NotImplementedError

    @cached_property
    def scriptpath(self):
        return self.get_scriptpath()

    def get_scriptpath(self):
        return xbmcvfs.translatePath(self.window_file_class.basefolder)

    @cached_property
    def window_kwargs(self):
        return self.get_window_kwargs()

    def get_window_kwargs(self):
        return {}

    def write(self):
        for window_file in self.window_files:
            window_file.write()

    def get_window(self):
        filename = self.window_file_class.filename
        return self.window_class(filename, self.scriptpath, 'Default', '1080i', **self.window_kwargs)

    def get_result(self, window):
        return None

    def run(self):
        self.write()
        window = self.get_window()
        window.doModal()
        result = self.get_result(window)
        del window
        return result
