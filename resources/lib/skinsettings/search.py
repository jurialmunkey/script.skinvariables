# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import re
import xbmc
from jurialmunkey.ftools import cached_property
from resources.lib.skinsettings.items import (
    DefinitionItem,
    SkinSettingsCategory,
    PROPERTY_PREFIX,
    SEARCH_PROPERTY_PREFIX,
)


SEARCH_KEY = 'SkinVariables.Search'
SEARCH_EDIT_ID = -300000
# Global search keeps the skin's edit template control where the skin placed it, including its id.
PLACED_EDIT_ID = 12
QUERY_PROPERTY = f'{SEARCH_PROPERTY_PREFIX}.Query'
TOP_CONTROL_PROPERTY = f'{PROPERTY_PREFIX}.TopControlID'
BOTTOM_CONTROL_PROPERTY = f'{PROPERTY_PREFIX}.BottomControlID'
WINDOW_PROPERTY_REGEX = re.compile(r'\bWindow\.Property\(', re.IGNORECASE)


class SearchBase:
    """Search hooks used by the definition, template and window. The defaults add no search behaviour."""

    @property
    def categories(self):
        return []

    @property
    def list_items(self):
        return []

    @property
    def placed_items(self):
        return []

    def get_shown_condition(self, item):
        return item.category.condition

    def onchangecategory(self, window):
        pass

    def onchangeview(self, window):
        pass


class SearchDisabled(SearchBase):
    """Stands in for the search when the definition does not enable it."""


class SearchMode(SearchBase):
    """Shared behaviour of the search modes. Subclasses decide where the edit control and the results appear."""

    default_label = '$LOCALIZE[137]'

    @property
    def label(self):
        return str(self.meta.get('label', self.default_label))

    def get_shown_condition(self, item):
        raise NotImplementedError


class SearchEditControl:
    """Edit control that searches the settings each time its text changes."""

    template = 'edit'

    @property
    def hinttext_overrides(self):
        return [('hinttext', str(self.meta['hinttext']), {})] if 'hinttext' in self.meta else []

    def get_overrides(self):
        return super().get_overrides() + self.hinttext_overrides

    def onclick(self, window):
        # Edit controls send a click each time their text changes.
        window.set_search(window.get_text(self.control_id))


class SearchCategory(SearchEditControl, SearchMode, SkinSettingsCategory):
    """Search shown as the first category using the edit template. Its settings area shows the matching settings."""

    def __init__(self, meta):
        super().__init__(SEARCH_KEY, meta, 0)

    @property
    def categories(self):
        return [self]

    def get_shown_condition(self, item):
        return f'[{item.category.condition}] | [{self.condition} + {item.match_condition}]'


class LocalSearch(SearchMode):
    """Edit control at the top of every category that filters the settings of the selected category."""

    edit_control_id = SEARCH_EDIT_ID
    inactive_condition = f'String.IsEmpty(Window.Property({QUERY_PROPERTY}))'

    def __init__(self, meta):
        self.meta = meta

    @cached_property
    def edit(self):
        return SearchEdit(self)

    @property
    def list_items(self):
        return [self.edit]

    def get_shown_condition(self, item):
        return f'[{item.category.condition}] + [[{self.inactive_condition}] | [{item.match_condition}]]'

    def onchangecategory(self, window):
        window.set_text(self.edit.control_id, '')
        window.set_search('')


class GlobalSearch(LocalSearch):
    """Edit control placed by the skin that searches the settings of all categories.

    The first and last focusable settings in view are set as window properties so the skin can move focus between
    its edit control and the settings list.
    """

    edit_control_id = PLACED_EDIT_ID

    @property
    def list_items(self):
        return []

    @property
    def placed_items(self):
        return [self.edit]

    def get_shown_condition(self, item):
        return f'[[{item.category.condition}] + [{self.inactive_condition}]] | [{item.match_condition}]'

    def onchangeview(self, window):
        window.set_view_bounds()


class SearchEdit(SearchEditControl, DefinitionItem):
    def __init__(self, search):
        super().__init__('search', search.meta, 0, search)

    @property
    def search(self):
        return self.parent

    @property
    def control_id(self):
        return self.search.edit_control_id

    @property
    def label(self):
        return self.search.label


SEARCH_MODES = {
    'category': SearchCategory,
    'local': LocalSearch,
    'global': GlobalSearch,
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


class SettingsViewBounds:
    """Finds the first and last focusable settings in the current view. Evaluate after the view properties are set."""

    def __init__(self, settings, window_id):
        self.settings = settings
        self.window_id = window_id

    def get_window_condition(self, condition):
        # Kodi evaluates script conditions against the topmost modal dialog when one is open, such as the keyboard.
        return WINDOW_PROPERTY_REGEX.sub(f'Window({self.window_id}).Property(', condition)

    @cached_property
    def focusable_ids(self):
        return self.get_focusable_ids()

    def get_focusable_ids(self):
        return [
            setting.control_id
            for setting in self.settings
            if xbmc.getCondVisibility(self.get_window_condition(setting.focusable_condition))
        ]

    @cached_property
    def properties(self):
        return self.get_properties()

    def get_properties(self):
        bounds = [str(self.focusable_ids[0]), str(self.focusable_ids[-1])] if self.focusable_ids else ['', '']
        return dict(zip((TOP_CONTROL_PROPERTY, BOTTOM_CONTROL_PROPERTY), bounds))
