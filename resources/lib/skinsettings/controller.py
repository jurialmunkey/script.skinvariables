# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.scriptwindow.controller import ScriptWindowController, ScriptWindowFile
from resources.lib.skinsettings.definition import SkinSettingsDefinition
from resources.lib.skinsettings.state import SkinSettingsViewState
from resources.lib.skinsettings.template import get_skinsettings_template
from resources.lib.skinsettings.window import SkinSettingsWindow


class SkinSettingsWindowFile(ScriptWindowFile):
    basefolder = 'special://profile/addon_data/script.skinvariables/skinsettings/'
    filename = 'script-skinvariables-skinsettings-generated.xml'

    def __init__(self, folder, definition):
        super().__init__(folder)
        self.definition = definition

    def get_template(self):
        return get_skinsettings_template(self.folder, self.definition)


class SkinSettingsController(ScriptWindowController):
    window_file_class = SkinSettingsWindowFile
    window_class = SkinSettingsWindow

    def __init__(self, filepath):
        self.filepath = filepath

    @cached_property
    def definition(self):
        return SkinSettingsDefinition(self.filepath)

    def get_window_file(self, folder):
        return SkinSettingsWindowFile(folder, self.definition)

    def get_window_kwargs(self):
        return {'definition': self.definition}

    def get_view_state(self):
        """View of the newly opened window."""
        return SkinSettingsViewState()

    def run(self):
        # Kodi keeps the window open when the skin reloads so the window restores its own view.
        self.write()
        return self.show(view_state=self.get_view_state())


def run_skinsettings(run_skinsettings, **kwargs):
    SkinSettingsController(run_skinsettings).run()
