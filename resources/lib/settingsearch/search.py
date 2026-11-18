# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from jurialmunkey.ftools import cached_property
from resources.lib.settingsearch.kodisettings import SETTING_LEVELS
from resources.lib.skinsettings.items import DefinitionItem, PROPERTY_PREFIX
from resources.lib.skinsettings.search import GlobalSearch, SettingsSearch


LEVEL_BUTTON_ID = 20
LEVEL_PROPERTY = f'{PROPERTY_PREFIX}.Level'
LEVEL_LABEL_PROPERTY = f'{PROPERTY_PREFIX}.LevelLabel'
# Kodi labels its settings levels with consecutive ids from Basic to Expert.
LEVEL_LABEL_ID_START = 10036


class SettingLevel:
    """Settings level that the search shows settings up to, as its position from Basic to Expert."""

    def __init__(self, rank):
        self.rank = rank

    @property
    def label(self):
        return xbmc.getLocalizedString(LEVEL_LABEL_ID_START + self.rank)

    @property
    def next(self):
        return SettingLevel((self.rank + 1) % len(SETTING_LEVELS))

    @property
    def properties(self):
        return {LEVEL_PROPERTY: str(self.rank), LEVEL_LABEL_PROPERTY: self.label}


class SettingSearchMode(GlobalSearch):
    """Edit control placed by the skin that searches every setting. Settings only show while they match the search.

    The skin can also place a tags button that filters by window and category labels and a level button that
    changes the settings level the search shows.
    """

    def __init__(self):
        super().__init__({'tags': {}})

    @cached_property
    def level_buttons(self):
        return self.get_level_buttons()

    def get_level_buttons(self):
        return [SearchLevelButton(self)]

    @property
    def placed_items(self):
        return super().placed_items + self.level_buttons

    def get_shown_condition(self, item):
        return item.match_condition

    def get_tag_settings(self, window, settings):
        return [setting for setting in settings if setting.is_listed(window.level.rank)]


class SearchLevelButton(DefinitionItem):
    """Button placed by the skin that moves the settings level the search shows to the next level."""

    control_id_start = LEVEL_BUTTON_ID
    template = 'level'

    def __init__(self, search):
        super().__init__('level', {}, 0, search)

    @property
    def label(self):
        return f'$INFO[Window.Property({LEVEL_LABEL_PROPERTY})]'

    def onclick(self, window):
        window.set_level(window.level.next)
        window.update_search()


class SettingSearchMatches(SettingsSearch):
    """Matches the settings listed at the settings level. Headings match while one of their settings matches."""

    def __init__(self, query, tag, level, headings, settings):
        super().__init__(query, tag, headings, settings)
        self.level = level

    def is_match(self, setting):
        return setting.is_listed(self.level.rank) and super().is_match(setting)
