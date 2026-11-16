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
    get_label_text,
)


SEARCH_KEY = 'SkinVariables.Search'
SEARCH_EDIT_ID = -300000
# Global search keeps the skin's edit template control where the skin placed it, including its id.
PLACED_EDIT_ID = 12
TAGS_BUTTON_ID = 17
QUERY_PROPERTY = f'{SEARCH_PROPERTY_PREFIX}.Query'
TAG_PROPERTY = f'{SEARCH_PROPERTY_PREFIX}.Tag'
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

    def onchoosetag(self, window):
        pass


class SearchDisabled(SearchBase):
    """Stands in for the search when the definition does not enable it."""


class SearchMode(SearchBase):
    """Shared behaviour of the search modes. Subclasses decide where the edit control and the results appear."""

    default_label = '$LOCALIZE[137]'

    @property
    def label(self):
        return str(self.meta.get('label', self.default_label))

    @cached_property
    def tags_buttons(self):
        """Tags button placed by the skin when the search definition has tags."""
        return self.get_tags_buttons()

    def get_tags_buttons(self):
        return [SearchTagsButton(self)] if 'tags' in self.meta else []

    @property
    def placed_items(self):
        return self.tags_buttons

    def get_shown_condition(self, item):
        raise NotImplementedError


class SearchEditControl:
    """Edit control that searches the settings each time its text changes."""

    template = 'edit'

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

    def onchoosetag(self, window):
        # Matching settings only show in the search category so choosing a tag selects it.
        window.set_category(self.key)


class LocalSearch(SearchMode):
    """Edit control at the top of every category that filters the settings of the selected category."""

    edit_control_id = SEARCH_EDIT_ID
    inactive_condition = (
        f'String.IsEmpty(Window.Property({QUERY_PROPERTY})) + String.IsEmpty(Window.Property({TAG_PROPERTY}))'
    )

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
        window.clear_search()


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
        return [self.edit] + super().placed_items

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


class SearchTagsButton(DefinitionItem):
    """Button placed by the skin that lists the tags of the settings in view to filter the settings by tag."""

    control_id_start = TAGS_BUTTON_ID
    template = 'tags'
    default_label = '$LOCALIZE[20459]'

    def __init__(self, search):
        super().__init__('tags', search.meta['tags'], 0, search)

    @property
    def label(self):
        return str(self.meta.get('label', self.default_label))

    def onclick(self, window):
        window.choose_tag(self.label_text)


SEARCH_MODES = {
    'category': SearchCategory,
    'local': LocalSearch,
    'global': GlobalSearch,
}


def get_search(meta):
    return SEARCH_MODES[meta.get('mode', 'category')](meta)


class SettingsSearch:
    """Matches settings with the selected tag whose label, group label, description or tags contain every term."""

    def __init__(self, query, tag, groups, settings):
        self.query = query
        self.tag = tag
        self.groups = groups
        self.settings = settings

    @cached_property
    def terms(self):
        return self.query.lower().split()

    @cached_property
    def is_active(self):
        return bool(self.terms or self.tag)

    def is_tag_match(self, setting):
        return not self.tag or self.tag in setting.tags

    def is_terms_match(self, setting):
        search_text = setting.search_text
        return all(term in search_text for term in self.terms)

    def is_match(self, setting):
        return self.is_tag_match(setting) and self.is_terms_match(setting)

    @cached_property
    def matched_settings(self):
        return self.get_matched_settings()

    def get_matched_settings(self):
        if not self.is_active:
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
        return {
            QUERY_PROPERTY: ' '.join(self.terms),
            TAG_PROPERTY: get_label_text(self.tag),
            **self.match_properties,
        }


class SettingsVisibility:
    """Evaluates the conditions of settings against the window. Evaluate after the view properties are set."""

    def __init__(self, settings, window_id):
        self.settings = settings
        self.window_id = window_id

    def get_window_condition(self, condition):
        # Kodi evaluates script conditions against the topmost modal dialog when one is open, such as the keyboard.
        return WINDOW_PROPERTY_REGEX.sub(f'Window({self.window_id}).Property(', condition)

    def is_visible(self, condition):
        return xbmc.getCondVisibility(self.get_window_condition(condition))


class SettingsViewBounds(SettingsVisibility):
    """Finds the first and last focusable settings in the current view."""

    @cached_property
    def focusable_ids(self):
        return self.get_focusable_ids()

    def get_focusable_ids(self):
        return [
            setting.control_id
            for setting in self.settings
            if self.is_visible(setting.focusable_condition)
        ]

    @cached_property
    def properties(self):
        return self.get_properties()

    def get_properties(self):
        bounds = [str(self.focusable_ids[0]), str(self.focusable_ids[-1])] if self.focusable_ids else ['', '']
        return dict(zip((TOP_CONTROL_PROPERTY, BOTTOM_CONTROL_PROPERTY), bounds))


class SettingsTags(SettingsVisibility):
    """Tags to choose from with the tags button, sorted by label. Offers to clear the selected tag first.

    Lists the tags of every setting until search terms are entered, then the tags of the settings in view.
    """

    clear_label_id = 231

    def __init__(self, search, window_id):
        super().__init__(search.settings, window_id)
        self.search = search

    @cached_property
    def tag_settings(self):
        return self.get_tag_settings()

    def get_tag_settings(self):
        if not self.search.terms:
            return self.settings
        return [setting for setting in self.settings if self.is_visible(setting.visible)]

    @cached_property
    def tags(self):
        return self.get_tags()

    def get_tags(self):
        labels = {
            tag: get_label_text(tag)
            for setting in self.tag_settings
            for tag in setting.tags
        }
        return sorted(labels.items(), key=lambda item: item[1].casefold())

    @cached_property
    def choices(self):
        """Tags with their labels. An empty tag clears the selected tag."""
        return self.get_choices()

    def get_choices(self):
        clear = [('', xbmc.getLocalizedString(self.clear_label_id))] if self.search.tag else []
        return clear + self.tags

    @property
    def labels(self):
        return [label for tag, label in self.choices]

    @property
    def preselect(self):
        return next((position for position, (tag, label) in enumerate(self.choices) if tag == self.search.tag), -1)

    def get_tag(self, position):
        return self.choices[position][0]
