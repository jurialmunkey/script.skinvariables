# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmcgui
from jurialmunkey.ftools import cached_property
from resources.lib.scriptwindow.window import ScriptWindow, ScriptWindowMixin
from resources.lib.skinsettings.items import CATEGORY_LABEL_PROPERTY, CATEGORY_PROPERTY
from resources.lib.skinsettings.search import SettingsSearch, SettingsTags, SettingsViewBounds
from resources.lib.skinsettings.state import SavedViewState


DESCRIPTION_CONTROL_ID = 6


class SettingsWindowMixin(ScriptWindowMixin):
    """Lists settings from a definition and searches them in a window or dialog. Subclasses arrange the view."""

    def __init__(self, *args, definition=None, view_state=None, **kwargs):
        self.definition = definition
        self.view_state = view_state
        self.search_query = ''
        self.search_tag = ''

    @property
    def controls(self):
        return self.definition.controls

    def set_description(self, text):
        self.getControl(DESCRIPTION_CONTROL_ID).setText(text)

    def get_text(self, control_id):
        return self.getControl(control_id).getText()

    def set_text(self, control_id, text):
        self.getControl(control_id).setText(text)

    def get_slider_value(self, control_id):
        return self.getControl(control_id).getInt()

    def set_slider_value(self, control_id, value, maximum):
        self.getControl(control_id).setInt(value, 0, 1, maximum)

    def refresh_settings(self):
        for setting in self.definition.settings:
            setting.onrefresh(self)

    @property
    def settings_search(self):
        raise NotImplementedError

    def update_search(self):
        self.set_properties(self.settings_search.properties)

    def set_search(self, query):
        self.search_query = query
        self.update_search()
        self.definition.search.onchangesearch(self)

    def set_tag(self, tag):
        self.search_tag = tag
        self.update_search()
        self.definition.search.onchangesearch(self)

    def clear_search(self):
        self.search_query = ''
        self.search_tag = ''
        self.update_search()

    def restore_search(self, query, tag):
        """Show the search without the search mode reacting to it as a new search."""
        self.search_query = query
        self.search_tag = tag
        self.update_search()
        self.definition.search.onrestore(self)

    def choose_tag(self, heading):
        # Selecting the search view first lets the tags reflect the settings that the search shows.
        self.definition.search.onchoosetag(self)
        tag_settings = self.definition.search.get_tag_settings(self, self.definition.settings)
        tags = SettingsTags(self.settings_search, tag_settings, self.window_id)
        position = xbmcgui.Dialog().select(heading, tags.labels, preselect=tags.preselect)
        if position == -1:
            return
        self.set_tag(tags.get_tag(position))

    @cached_property
    def window_id(self):
        """Id of this window. Read on first use when this window is active, which dialogs over it do not change."""
        return self.get_window_id()

    def get_window_id(self):
        return xbmcgui.getCurrentWindowId()

    @property
    def view_settings(self):
        """Settings in list order that can be in view. The view bounds look for the focusable settings among them."""
        return self.definition.ordered_settings

    def set_view_bounds(self):
        self.set_properties(SettingsViewBounds(self.view_settings, self.window_id).properties)

    def onInit(self):
        self.refresh_settings()
        self.view_state.apply(self)

    def onFocus(self, control_id):
        # Settings can change while a dialog opened by a click is shown so moving focus also refreshes the view.
        super().onFocus(control_id)
        self.refresh_settings()
        self.definition.search.onchangeview(self)

    def onClick(self, control_id):
        # Clicks change the search text or skin settings that the settings visibility can depend on.
        super().onClick(control_id)
        self.definition.search.onchangeview(self)

    def onAction(self, action):
        # Kodi sends no click for some controls when select is pressed, such as sliders, so items receive it here.
        if action.getId() == xbmcgui.ACTION_SELECT_ITEM:
            self.get_item(self.getFocusId()).onselect(self)
        super().onAction(action)


class SkinSettingsWindow(SettingsWindowMixin, ScriptWindow):
    """Settings window that shows the settings of the selected category."""

    @property
    def category(self):
        """Key of the selected category."""
        return self.getProperty(CATEGORY_PROPERTY)

    def get_category_properties(self, key):
        # A view saved before any category had focus has no category to label.
        category = self.definition.categories_by_key.get(key)
        return {CATEGORY_PROPERTY: key, CATEGORY_LABEL_PROPERTY: category.label_text if category else ''}

    def set_category(self, key):
        # Returning focus to the selected category is not a change so the search mode decides whether it keeps the
        # search.
        if self.category == key:
            self.definition.search.onreturncategory(self)
            return
        self.set_properties(self.get_category_properties(key))
        self.definition.search.onchangecategory(self)
        self.definition.search.onchangeview(self)

    @property
    def settings_search(self):
        return SettingsSearch(self.search_query, self.search_tag, self.definition.groups, self.definition.settings)

    def restore_view(self, category, query, tag, properties):
        # Sets the category directly because changing it would clear the search that the view restores.
        self.set_properties({**properties, **self.get_category_properties(category)})
        self.restore_search(query, tag)

    def get_saved_view(self, focus_id):
        return SavedViewState(
            self.category,
            self.search_query,
            self.search_tag,
            self.definition.search.get_state_properties(self),
            focus_id,
        )

    def save_view(self, control_id):
        """Save the view that the window shows again when it initialises, such as after a skin reload."""
        self.view_state = self.get_saved_view(control_id)

    def onClick(self, control_id):
        # Skin reloads start from a click. Kodi focuses its first category when the window initialises after a
        # reload, so the view is saved here before that focus can change the category.
        self.save_view(control_id)
        super().onClick(control_id)

    def onAction(self, action):
        # Sliders run their actions when select is pressed rather than when clicked.
        if action.getId() == xbmcgui.ACTION_SELECT_ITEM:
            self.save_view(self.getFocusId())
        super().onAction(action)
