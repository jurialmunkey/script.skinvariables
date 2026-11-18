# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.settingsearch.items import (
    KodiHeading,
    SearchButtonSetting,
    SearchRadioButtonSetting,
    SearchSliderSetting,
    SkinHeading,
    get_kodi_setting_item,
)
from resources.lib.settingsearch.kodisettings import KodiSettingsTree
from resources.lib.settingsearch.search import SettingSearchMode
from resources.lib.skinsettings.definition import SkinSettingsDefinition
from resources.lib.skinsettings.items import link_settings


class SearchSkinSettingsDefinition(SkinSettingsDefinition):
    """Skin settings listed by the settings search. Its categories become headings placed after Kodi's headings.

    The search of the settings search replaces the search of the definition.
    """

    setting_classes = {
        'button': SearchButtonSetting,
        'radiobutton': SearchRadioButtonSetting,
        'slider': SearchSliderSetting,
    }

    def __init__(self, filepath, search, heading_offset):
        super().__init__(filepath)
        self.search_mode = search
        self.heading_offset = heading_offset

    def get_search(self):
        return self.search_mode

    def get_categories(self):
        return [
            SkinHeading(key, meta, rank + self.heading_offset, self.search)
            for rank, (key, meta) in self.get_entries('categories')
        ]


class NoSkinSettings:
    """Stands in for the skin settings when the settings search is opened without a skin settings definition."""

    categories = []
    settings = []


class SettingSearchDefinition:
    """Kodi's settings followed by the skin settings, each listed under the heading of its category."""

    def __init__(self, skinsettings=None):
        self.skinsettings = skinsettings

    @cached_property
    def search(self):
        return SettingSearchMode()

    @cached_property
    def kodi_tree(self):
        return KodiSettingsTree()

    @cached_property
    def kodi_headings(self):
        return self.get_kodi_headings()

    def get_kodi_headings(self):
        return [
            KodiHeading(category, rank, self.search)
            for rank, category in enumerate(self.kodi_tree.categories)
        ]

    @property
    def kodi_entries(self):
        """Kodi settings with their headings."""
        return (
            (heading, setting)
            for heading in self.kodi_headings
            for setting in heading.kodi_category.settings
        )

    @cached_property
    def kodi_settings(self):
        return self.get_kodi_settings()

    def get_kodi_settings(self):
        return link_settings([
            get_kodi_setting_item(setting, rank, heading, self.search)
            for rank, (heading, setting) in enumerate(self.kodi_entries)
        ])

    @cached_property
    def skin_definition(self):
        return self.get_skin_definition()

    def get_skin_definition(self):
        if not self.skinsettings:
            return NoSkinSettings()
        return SearchSkinSettingsDefinition(self.skinsettings, self.search, len(self.kodi_headings))

    @cached_property
    def headings(self):
        return self.get_headings()

    def get_headings(self):
        return self.kodi_headings + self.skin_definition.categories

    @cached_property
    def settings(self):
        return self.get_settings()

    def get_settings(self):
        return self.kodi_settings + self.skin_definition.settings

    @cached_property
    def layout(self):
        """Headings followed by their settings, ordered by heading then by setting."""
        return self.get_layout()

    def get_layout(self):
        return sorted(self.headings + self.settings, key=lambda item: item.order)

    @cached_property
    def controls(self):
        return self.get_controls()

    def get_controls(self):
        items = self.search.placed_items + self.headings + self.settings
        return {item.control_id: item for item in items}
