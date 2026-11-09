# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from json import loads
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import load_filecontent
from resources.lib.skinsettings.items import DefinitionEntries, SkinSettingsCategory, SkinSettingsGroup, SETTING_CLASSES
from resources.lib.skinsettings.search import SearchDisabled, get_search


class SkinSettingsDefinition:
    def __init__(self, filepath):
        self.filepath = filepath

    @cached_property
    def meta(self):
        return self.get_meta()

    def get_meta(self):
        return loads(str(load_filecontent(self.filepath)))

    def get_entries(self, section):
        return enumerate(DefinitionEntries(self.meta.get(section, {})).entries)

    @cached_property
    def search(self):
        return self.get_search()

    def get_search(self):
        if 'search' not in self.meta:
            return SearchDisabled()
        return get_search(self.meta['search'])

    @cached_property
    def categories(self):
        return self.get_categories()

    def get_categories(self):
        search_categories = self.search.categories
        offset = len(search_categories)
        return search_categories + [
            SkinSettingsCategory(key, meta, rank + offset)
            for rank, (key, meta) in self.get_entries('categories')
        ]

    @cached_property
    def categories_by_key(self):
        return {category.key: category for category in self.categories}

    @cached_property
    def groups(self):
        return self.get_groups()

    def get_groups(self):
        return [
            SkinSettingsGroup(key, meta, rank, self.categories_by_key[meta['category']], self.search)
            for rank, (key, meta) in self.get_entries('groups')
        ]

    @cached_property
    def groups_by_key(self):
        return {group.key: group for group in self.groups}

    @cached_property
    def settings(self):
        return self.get_settings()

    def get_settings(self):
        return [
            SETTING_CLASSES[meta['control']](key, meta, rank, self.groups_by_key[meta['group']], self.search)
            for rank, (key, meta) in self.get_entries('settings')
        ]

    @cached_property
    def layout(self):
        """Search controls, then group labels followed by their settings, ordered by category, group and setting."""
        return self.get_layout()

    def get_layout(self):
        return self.search.list_items + sorted(self.groups + self.settings, key=lambda item: item.order)

    @cached_property
    def ordered_settings(self):
        """Settings in the order they appear in the settings list."""
        return self.get_ordered_settings()

    def get_ordered_settings(self):
        return sorted(self.settings, key=lambda setting: setting.order)

    @cached_property
    def controls(self):
        return self.get_controls()

    def get_controls(self):
        items = self.categories + self.search.list_items + self.search.placed_items + self.groups + self.settings
        return {item.control_id: item for item in items}
