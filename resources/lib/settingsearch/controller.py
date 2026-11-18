# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.settingsearch.closeactions import NoCloseAction
from resources.lib.settingsearch.definition import SettingSearchDefinition
from resources.lib.settingsearch.kodisettings import KodiSettingLevel
from resources.lib.settingsearch.search import SettingLevel
from resources.lib.settingsearch.state import SettingSearchViewState
from resources.lib.settingsearch.template import get_settingsearch_template
from resources.lib.settingsearch.window import SettingSearchDialog
from resources.lib.skinsettings.controller import SkinSettingsController, SkinSettingsWindowFile


class SettingSearchWindowFile(SkinSettingsWindowFile):
    basefolder = 'special://profile/addon_data/script.skinvariables/settingsearch/'
    filename = 'script-skinvariables-settingsearch-generated.xml'

    def get_template(self):
        return get_settingsearch_template(self.folder, self.definition)


class SettingSearchController(SkinSettingsController):
    """Shows the settings search dialog. The skin settings definition is optional and adds the skin settings to it.

    Once the dialog closes for the last time, the controller runs its close action, such as opening a settings
    window or changing a setting that reloads the skin.
    """

    window_file_class = SettingSearchWindowFile
    window_class = SettingSearchDialog
    # Action that the last dialog shown asked to run after it closed.
    close_action = NoCloseAction()

    @cached_property
    def definition(self):
        return SettingSearchDefinition(self.filepath)

    def get_window_file(self, folder):
        return SettingSearchWindowFile(folder, self.definition)

    def get_result(self, window):
        self.close_action = window.close_action
        return super().get_result(window)

    def run(self):
        super().run()
        self.close_action.run()

    def get_view_state(self):
        # The search starts at the level of Kodi's settings windows so the settings it lists can be focused.
        return SettingSearchViewState(SettingLevel(KodiSettingLevel().rank))


def run_settingsearch(skinsettings=None, **kwargs):
    SettingSearchController(skinsettings).run()
