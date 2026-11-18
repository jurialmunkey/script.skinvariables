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
SCOPE_BUTTON_ID = 18
QUERY_PROPERTY = f'{SEARCH_PROPERTY_PREFIX}.Query'
TAG_PROPERTY = f'{SEARCH_PROPERTY_PREFIX}.Tag'
SCOPE_PROPERTY = f'{SEARCH_PROPERTY_PREFIX}.Local'
STORED_QUERY_PROPERTY = f'{SEARCH_PROPERTY_PREFIX}.StoredQuery'
STORED_TAG_PROPERTY = f'{SEARCH_PROPERTY_PREFIX}.StoredTag'
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

    def onreturncategory(self, window):
        pass

    def onchangeview(self, window):
        pass

    def onchangesearch(self, window):
        pass

    def onchoosetag(self, window):
        pass

    def get_tag_settings(self, window, settings):
        """Settings whose tags the tags button lists."""
        return settings

    def get_state_properties(self, window):
        """Window properties of the search mode that a reloaded view restores."""
        return {}

    def onrestore(self, window):
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

    def onrestore(self, window):
        window.set_text(self.control_id, window.search_query)


class LocalSearch(SearchMode):
    """Edit control at the top of every category that filters the settings of the selected category."""

    edit_control_id = SEARCH_EDIT_ID
    inactive_condition = (
        f'String.IsEmpty(Window.Property({QUERY_PROPERTY})) + String.IsEmpty(Window.Property({TAG_PROPERTY}))'
    )
    active_condition = (
        f'!String.IsEmpty(Window.Property({QUERY_PROPERTY})) | !String.IsEmpty(Window.Property({TAG_PROPERTY}))'
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

    def onrestore(self, window):
        window.set_text(self.edit.control_id, window.search_query)


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

    def onreturncategory(self, window):
        # Results replace the settings of the selected category so returning to it shows its settings again.
        self.onchangecategory(window)

    def onchangeview(self, window):
        window.set_view_bounds()


class SearchAllCategory(SkinSettingsCategory):
    """Category listed first by the mixed search that shows the settings of every category."""

    default_label = '$LOCALIZE[137]'

    def __init__(self, meta):
        super().__init__(SEARCH_KEY, meta, 0)

    @property
    def label(self):
        return str(self.meta.get('label', self.default_label))

    def onchangecategory(self, window):
        """Called by the mixed search when the selected category changes, before it clears the search."""

    def get_state_properties(self, window):
        """Window properties of the category that a reloaded view restores."""
        return {}


class SearchActiveCategory(SearchAllCategory):
    """Search category hidden until a search or tag is active. Stays shown while selected so the view keeps it.

    Changing category stores an active search and keeps the category shown. Selecting it again restores the stored
    search unless a new search selected it.
    """

    stored_properties = (STORED_QUERY_PROPERTY, STORED_TAG_PROPERTY)
    stored_condition = ' | '.join(f'!String.IsEmpty(Window.Property({name}))' for name in stored_properties)

    def __init__(self, meta, search):
        super().__init__(meta)
        self.search = search

    @cached_property
    def visible(self):
        return self.get_visible()

    def get_visible(self):
        return f'[{self.search.active_condition}] | [{self.condition}] | [{self.stored_condition}]'

    def get_overrides(self):
        return super().get_overrides() + [('visible', self.visible, {})]

    def set_stored(self, window, query, tag):
        window.set_properties(dict(zip(self.stored_properties, (query, tag))))

    def store_search(self, window):
        if not window.settings_search.is_active:
            return
        self.set_stored(window, window.search_query, window.search_tag)

    def restore_search(self, window):
        query, tag = (window.getProperty(name) for name in self.stored_properties)
        self.set_stored(window, '', '')
        if window.settings_search.is_active:
            return
        window.restore_search(query, tag)

    def onchangecategory(self, window):
        if window.category == self.key:
            self.restore_search(window)
            return
        self.store_search(window)

    def get_state_properties(self, window):
        return {name: window.getProperty(name) for name in self.stored_properties}


class MixedSearchScope:
    """Scope of the mixed search, stored as a window property value so the skin conditions can follow it."""

    property_value = ''
    toggle_value = ''

    def __init__(self, search):
        self.search = search

    def get_tag_settings(self, window, settings):
        raise NotImplementedError

    def onchangesearch(self, window):
        pass


class MixedGlobalScope(MixedSearchScope):
    """Searches every category. Entering a search or tag selects the search category to show the results."""

    toggle_value = 'true'

    def get_tag_settings(self, window, settings):
        return settings

    def onchangesearch(self, window):
        if not window.settings_search.is_active:
            return
        window.set_category(self.search.search_category.key)


class MixedLocalScope(MixedSearchScope):
    """Filters the selected category. The search category still filters every category and keeps the search."""

    property_value = 'true'

    def get_tag_settings(self, window, settings):
        return [
            setting
            for setting in settings
            if window.category in (self.search.search_category.key, setting.category.key)
        ]


class MixedSearch(GlobalSearch):
    """Edit control placed by the skin that searches every category from the search category.

    The search category shows the settings of every category until a search or tag filters them. Other categories
    show their own settings. By default a search or tag selects the search category to search every category. The
    skin can place a scope button that toggles to filtering the selected category instead.
    """

    scope_classes = (MixedGlobalScope, MixedLocalScope)
    local_condition = f'!String.IsEmpty(Window.Property({SCOPE_PROPERTY}))'
    global_condition = f'String.IsEmpty(Window.Property({SCOPE_PROPERTY}))'

    @cached_property
    def search_category(self):
        return self.get_search_category()

    def get_search_category(self):
        meta = self.meta.get('category', {})
        if meta.get('autohide'):
            return SearchActiveCategory(meta, self)
        return SearchAllCategory(meta)

    @property
    def categories(self):
        return [self.search_category]

    @cached_property
    def scope_buttons(self):
        """Scope button placed by the skin when the search definition has a scope."""
        return self.get_scope_buttons()

    def get_scope_buttons(self):
        return [SearchScopeButton(self)] if 'scope' in self.meta else []

    @property
    def placed_items(self):
        return super().placed_items + self.scope_buttons

    @cached_property
    def scopes(self):
        return self.get_scopes()

    def get_scopes(self):
        return {scope_class.property_value: scope_class(self) for scope_class in self.scope_classes}

    def get_scope(self, window):
        return self.scopes[window.getProperty(SCOPE_PROPERTY)]

    def toggle_scope(self, window):
        window.setProperty(SCOPE_PROPERTY, self.get_scope(window).toggle_value)
        self.onchangesearch(window)

    def get_shown_condition(self, item):
        results_condition = f'[{self.search_category.condition}] | [{item.category.condition} + {self.local_condition}]'
        search_condition = f'[{self.inactive_condition}] | [{item.match_condition}]'
        category_condition = f'[{item.category.condition}] + [{self.inactive_condition}]'
        return f'[[{results_condition}] + [{search_condition}]] | [{category_condition}]'

    def is_search_category(self, window):
        return window.category == self.search_category.key

    def onchangecategory(self, window):
        self.search_category.onchangecategory(window)
        # The search category shows the results so selecting it keeps the search.
        if self.is_search_category(window):
            return
        super().onchangecategory(window)

    def onreturncategory(self, window):
        # Results show in the search category rather than replacing the selected category so the search is kept.
        pass

    def onchangesearch(self, window):
        self.get_scope(window).onchangesearch(window)

    def get_tag_settings(self, window, settings):
        return self.get_scope(window).get_tag_settings(window, settings)

    def get_state_properties(self, window):
        return {SCOPE_PROPERTY: window.getProperty(SCOPE_PROPERTY), **self.search_category.get_state_properties(window)}


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


class SearchScopeButton(DefinitionItem):
    """Radiobutton placed by the skin that toggles the mixed search between every category and the selected one.

    Selected while the search covers every category.
    """

    control_id_start = SCOPE_BUTTON_ID
    template = 'scope'

    def __init__(self, search):
        super().__init__('scope', search.meta['scope'], 0, search)

    @property
    def search(self):
        return self.parent

    def get_overrides(self):
        return super().get_overrides() + [('selected', self.search.global_condition, {})]

    def onclick(self, window):
        self.search.toggle_scope(window)


SEARCH_MODES = {
    'category': SearchCategory,
    'local': LocalSearch,
    'global': GlobalSearch,
    'mixed': MixedSearch,
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
        return [setting.label_item for setting in self.matched_settings]

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

    Lists the tags of the given settings until search terms are entered, then the tags of those in view.
    """

    clear_label_id = 231

    def __init__(self, search, settings, window_id):
        super().__init__(settings, window_id)
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
