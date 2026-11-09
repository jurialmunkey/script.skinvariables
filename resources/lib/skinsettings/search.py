# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.skinsettings.items import DefinitionItem, SkinSettingsCategory


SEARCH_KEY = 'SkinVariables.Search'
SEARCH_EDIT_ID = -300000


class SearchDisabled:
    """Stands in for the search category when the definition does not enable search."""

    @property
    def categories(self):
        return []

    @property
    def list_items(self):
        return []

    def get_result_conditions(self, item):
        return []


class SearchCategory(SkinSettingsCategory):
    """First category of the window. Its settings area shows the search edit control and the matching settings."""

    default_label = '$LOCALIZE[137]'

    def __init__(self, meta):
        super().__init__(SEARCH_KEY, meta, 0)

    @property
    def label(self):
        return str(self.meta.get('label', self.default_label))

    @cached_property
    def edit(self):
        return SearchEdit(self)

    @property
    def categories(self):
        return [self]

    @property
    def list_items(self):
        return [self.edit]

    def get_result_conditions(self, item):
        return [f'{self.condition} + !String.IsEmpty(Window.Property({item.search_property}))']


class SearchEdit(DefinitionItem):
    control_id_start = SEARCH_EDIT_ID
    template = 'edit'

    def __init__(self, category):
        super().__init__(category.key, category.meta, 0, category)

    @property
    def category(self):
        return self.parent

    @property
    def label(self):
        return self.category.label

    def get_overrides(self):
        hinttext = [('hinttext', str(self.meta['hinttext']), {})] if 'hinttext' in self.meta else []
        return super().get_overrides() + [('visible', self.category.condition, {})] + hinttext

    def onclick(self, window):
        # Edit controls send a click each time their text changes.
        window.set_search(window.get_text(self.control_id))


class SettingsSearch:
    """Matches settings whose label, group label or description contain every search term."""

    def __init__(self, query, groups, settings):
        self.query = query
        self.groups = groups
        self.settings = settings

    @cached_property
    def terms(self):
        return self.query.lower().split()

    def is_match(self, setting):
        search_text = setting.search_text
        return all(term in search_text for term in self.terms)

    @cached_property
    def matched_settings(self):
        return self.get_matched_settings()

    def get_matched_settings(self):
        if not self.terms:
            return []
        return [setting for setting in self.settings if self.is_match(setting)]

    @cached_property
    def matched_groups(self):
        return self.get_matched_groups()

    def get_matched_groups(self):
        return [setting.group for setting in self.matched_settings]

    @cached_property
    def matched_items(self):
        return self.get_matched_items()

    def get_matched_items(self):
        return set(self.matched_groups + self.matched_settings)

    @cached_property
    def properties(self):
        return self.get_properties()

    def get_properties(self):
        return {
            item.search_property: 'true' if item in self.matched_items else ''
            for item in self.groups + self.settings
        }
