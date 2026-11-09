# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.skinsettings.items import DefinitionItem, SkinSettingsCategory, SEARCH_PROPERTY_PREFIX


SEARCH_KEY = 'SkinVariables.Search'
SEARCH_EDIT_ID = -300000
QUERY_PROPERTY = f'{SEARCH_PROPERTY_PREFIX}.Query'


class SearchDisabled:
    """Stands in for the search when the definition does not enable it."""

    @property
    def categories(self):
        return []

    @property
    def list_items(self):
        return []

    def get_shown_condition(self, item):
        return item.category.condition

    def onchangecategory(self, window):
        pass


class SearchMode:
    """Shared behaviour of the search modes. Subclasses decide where the edit control and the results appear."""

    default_label = '$LOCALIZE[137]'

    @property
    def label(self):
        return str(self.meta.get('label', self.default_label))

    @cached_property
    def edit(self):
        return SearchEdit(self)

    @property
    def categories(self):
        return []

    @property
    def list_items(self):
        return [self.edit]

    @property
    def edit_overrides(self):
        return []

    def get_shown_condition(self, item):
        raise NotImplementedError

    def onchangecategory(self, window):
        pass


class SearchCategory(SearchMode, SkinSettingsCategory):
    """Search shown as the first category. Its settings area shows the edit control and the matching settings."""

    def __init__(self, meta):
        super().__init__(SEARCH_KEY, meta, 0)

    @property
    def categories(self):
        return [self]

    @property
    def edit_overrides(self):
        return [('visible', self.condition, {})]

    def get_shown_condition(self, item):
        return f'[{item.category.condition}] | [{self.condition} + {item.match_condition}]'


class LocalSearch(SearchMode):
    """Edit control at the top of every category that filters the settings of the selected category."""

    inactive_condition = f'String.IsEmpty(Window.Property({QUERY_PROPERTY}))'

    def __init__(self, meta):
        self.meta = meta

    def get_shown_condition(self, item):
        return f'[{item.category.condition}] + [[{self.inactive_condition}] | [{item.match_condition}]]'

    def onchangecategory(self, window):
        window.set_text(self.edit.control_id, '')
        window.set_search('')


class GlobalSearch(LocalSearch):
    """Edit control at the top of every category that searches the settings of all categories."""

    def get_shown_condition(self, item):
        return f'[[{item.category.condition}] + [{self.inactive_condition}]] | [{item.match_condition}]'


class SearchEdit(DefinitionItem):
    control_id_start = SEARCH_EDIT_ID
    template = 'edit'

    def __init__(self, search):
        super().__init__('search', search.meta, 0, search)

    @property
    def search(self):
        return self.parent

    @property
    def label(self):
        return self.search.label

    def get_overrides(self):
        hinttext = [('hinttext', str(self.meta['hinttext']), {})] if 'hinttext' in self.meta else []
        return super().get_overrides() + self.search.edit_overrides + hinttext

    def onclick(self, window):
        # Edit controls send a click each time their text changes.
        window.set_search(window.get_text(self.control_id))


INLINE_SEARCH_LEVELS = {
    'local': LocalSearch,
    'global': GlobalSearch,
}


def get_inline_search(meta):
    return INLINE_SEARCH_LEVELS[meta.get('level', 'local')](meta)


SEARCH_MODES = {
    'category': SearchCategory,
    'inline': get_inline_search,
}


def get_search(meta):
    return SEARCH_MODES[meta.get('mode', 'category')](meta)


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
    def match_properties(self):
        return self.get_match_properties()

    def get_match_properties(self):
        return {
            item.search_property: 'true' if item in self.matched_items else ''
            for item in self.groups + self.settings
        }

    @cached_property
    def properties(self):
        return self.get_properties()

    def get_properties(self):
        return {QUERY_PROPERTY: ' '.join(self.terms), **self.match_properties}
