# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import threading
import xbmc
import xbmcgui
from jurialmunkey.ftools import cached_property
from resources.lib.kodiutils import get_localized
from resources.lib.multisearch.constants import PROPERTY_PREFIX
from resources.lib.multisearch.keyboard import KEYBOARD_KEYS
from resources.lib.multisearch.view import get_count_label
from resources.lib.multisearch.workers import EMPTY_REQUEST
from resources.lib.scriptwindow.window import ScriptWindow


EDIT_ID = 100
KEYBOARD_ID = 101
SOURCES_ID = 102
SORT_ID = 103
GENRE_ID = 104
DECADE_ID = 105
RESET_ID = 106
MEDIATYPE_ID = 107
HIDE_UNAIRED_ID = 108
SORT_PROPERTY = f'{PROPERTY_PREFIX}.SortBy'
BUSY_PROPERTY = f'{PROPERTY_PREFIX}.Busy'
SOURCES_ENABLED_PROPERTY = f'{PROPERTY_PREFIX}.Sources.Enabled'
SOURCES_TOTAL_PROPERTY = f'{PROPERTY_PREFIX}.Sources.Total'
MOVE_ACTIONS = (
    xbmcgui.ACTION_MOVE_LEFT,
    xbmcgui.ACTION_MOVE_RIGHT,
    xbmcgui.ACTION_MOVE_UP,
    xbmcgui.ACTION_MOVE_DOWN,
)


class MultiSearchControl:
    """Skin control of the multi search window that passes its clicks and actions to the window."""

    control_id = 0

    def onfocus(self, window):
        pass

    def onclick(self, window):
        pass

    def onaction(self, window, action_id):
        pass


class SearchEditControl(MultiSearchControl):
    control_id = EDIT_ID

    def onclick(self, window):
        # Edit controls send a click each time their text changes, after Kodi has updated the text.
        window.run_search(window.query)


class KeyboardControl(MultiSearchControl):
    control_id = KEYBOARD_ID

    def onclick(self, window):
        window.press_key()

    def onaction(self, window, action_id):
        if action_id in MOVE_ACTIONS:
            window.search.extend_wait()


class SourcesButton(MultiSearchControl):
    """Button that opens the sources dialog. The skin builds its label from the source count properties."""

    control_id = SOURCES_ID

    @staticmethod
    def get_properties(sources):
        return {
            SOURCES_ENABLED_PROPERTY: str(len(sources.enabled_positions)),
            SOURCES_TOTAL_PROPERTY: str(len(sources.items)),
        }

    def set_properties(self, window):
        window.set_properties(self.get_properties(window.search.sources))

    def onclick(self, window):
        window.select_sources()
        self.set_properties(window)


class SortButton(MultiSearchControl):
    control_id = SORT_ID

    def onclick(self, window):
        window.select_sort()


class FilterButton(MultiSearchControl):
    """Optional button that opens a select dialog to filter the results by a value found in them."""

    filter_name = ''

    def onclick(self, window):
        window.select_filter(window.search.filters.get(self.filter_name))


class GenreButton(FilterButton):
    control_id = GENRE_ID
    filter_name = 'genre'


class DecadeButton(FilterButton):
    control_id = DECADE_ID
    filter_name = 'decade'


class MediaTypeButton(FilterButton):
    control_id = MEDIATYPE_ID
    filter_name = 'mediatype'


class ToggleFilterButton(FilterButton):
    """Optional button that switches a filter on and off. The skin shows its state from the filter property."""

    def onclick(self, window):
        window.toggle_filter(window.search.filters.get(self.filter_name))


class HideUnairedButton(ToggleFilterButton):
    control_id = HIDE_UNAIRED_ID
    filter_name = 'unaired'


class ResetButton(MultiSearchControl):
    """Optional button that clears the search text and returns the filters and sources to their defaults."""

    control_id = RESET_ID

    def onclick(self, window):
        window.reset_options()


class ResultsControl(MultiSearchControl):
    """Results container. The skin can define a container for each widget style of the results."""

    def __init__(self, control_id):
        self.control_id = control_id

    def onclick(self, window):
        window.open_result(self.control_id)

    def onaction(self, window, action_id):
        # Python windows skip the media window actions so Kodi does not open the info dialog itself.
        if action_id == xbmcgui.ACTION_SHOW_INFO:
            window.show_info(self.control_id)


UNFOCUSED_CONTROL = MultiSearchControl()
MULTISEARCH_CONTROLS = {
    control.control_id: control
    for control in (
        SearchEditControl(),
        KeyboardControl(),
        SourcesButton(),
        SortButton(),
        GenreButton(),
        DecadeButton(),
        MediaTypeButton(),
        HideUnairedButton(),
        ResetButton(),
    )
}


class MultiSearchWindow(ScriptWindow):
    """Searches the enabled sources each time the search text changes and lists the combined results.

    Results arrive from the search workers so changes to the results list are made while holding the lock.
    The focused source button decides whether the list shows the results of all sources, of one content type or of one
    source.
    The content type, genre, decade and unaired filters narrow the results of each source before they are combined and limited.
    Changing the filters or sort method searches again so discover sources can look up results for them.
    The results are added to the container for their most common widget style and the other containers are emptied.
    When the window has a list for each content type, those lists are filled alongside the list of all results.
    """

    def __init__(
        self,
        *args,
        search=None,
        buttons=None,
        lists=None,
        opening_query=None,
        stored_query=None,
        **kwargs,
    ):
        self.search = search
        self.buttons = buttons
        self.lists = lists
        self.opening_query = opening_query
        self.stored_query = stored_query
        # Latest search text. Kodi applies setText later on the GUI thread so getText can still return the old text.
        self.text = ''
        self.view = search.get_view(EMPTY_REQUEST)
        self.lists.selected_list.button = buttons.get_default_button(self.view)
        # List and position of the result opened from the lists, which is focused again when the window returns.
        self.opened_list = None
        self.opened_position = None
        self.lock = threading.Lock()

    @property
    def selected_button(self):
        return self.lists.selected_list.button

    @cached_property
    def results_controls(self):
        return self.get_results_controls()

    def get_results_controls(self):
        return {control_id: ResultsControl(control_id) for control_id in self.lists.control_ids}

    @cached_property
    def controls(self):
        return {**MULTISEARCH_CONTROLS, **self.results_controls, **self.buttons.controls}

    @property
    def query(self):
        return self.getControl(EDIT_ID).getText()

    def onInit(self):
        # Kodi calls onInit again when returning from a window opened from the results.
        self.fill_keyboard()
        self.set_sort_property()
        self.controls[SOURCES_ID].set_properties(self)
        self.set_properties(self.selected_button.focus_properties)
        self.set_properties(self.search.filters.properties)
        with self.lock:
            self.update_buttons()
            self.fill_results()
            self.restore_focus()
        self.restore_query()

    def restore_focus(self):
        """Focus the result opened from the list again when returning from its window.

        Kodi reloads the window controls when returning so its own focus restore finds the results list empty.
        """
        if self.opened_list is None:
            return
        results_list, self.opened_list = self.opened_list, None
        if not results_list.results:
            return
        self.setFocusId(results_list.control_id)
        self.getControl(results_list.control_id).selectItem(min(self.opened_position, len(results_list.results) - 1))

    def restore_query(self):
        """Fill the edit control with the opening search text the first time the window opens.

        Kodi keeps the edit control text when returning from a window opened from the results.
        """
        if self.opening_query is None:
            return
        query, self.opening_query = self.opening_query, None
        self.set_text(query)

    def onAction(self, action):
        self.controls.get(self.getFocusId(), UNFOCUSED_CONTROL).onaction(self, action.getId())
        super().onAction(action)

    def fill_keyboard(self):
        control = self.getControl(KEYBOARD_ID)
        control.reset()
        control.addItems([key.listitem for key in KEYBOARD_KEYS])

    def set_sort_property(self):
        self.setProperty(SORT_PROPERTY, self.search.sort_method.get_label())

    def fill_list(self, results_list):
        """Fill the container for the results of the list. The container it filled before is emptied."""
        self.getControl(results_list.control_id).reset()
        results_list.set_results(self.view)
        control = self.getControl(results_list.control_id)
        control.reset()
        control.addItems([result.listitem for result in results_list.results])
        self.set_properties(results_list.properties)

    def fill_results(self):
        for results_list in self.lists.items:
            self.fill_list(results_list)

    def set_selected_button(self, button):
        self.set_properties(button.focus_properties)
        self.lists.selected_list.button = button

    def update_buttons(self):
        """Show the buttons with distinct results. The list returns to the first shown button if the selected button is
        hidden.
        """
        self.set_properties(self.buttons.get_shown_properties(self.view))
        if not self.selected_button.is_shown(self.search.sources, self.view):
            self.set_selected_button(self.buttons.get_default_button(self.view))

    def set_view(self, view):
        self.view = view
        self.update_buttons()
        self.fill_results()

    def refresh_view(self):
        """Show the shown search again after the sources, sort method or filters change."""
        self.set_view(self.search.get_view(self.view.request))

    def set_request(self, request):
        """Show the current search. It has finished so the busy property is cleared."""
        self.set_view(self.search.get_view(request))
        self.setProperty(BUSY_PROPERTY, '')

    def show_results(self, request):
        """Called by a search worker. Results of searches replaced by a later search are discarded."""
        with self.lock:
            if not self.search.is_current(request):
                return
            self.set_request(request)

    def set_text(self, text):
        """Set the edit control text and search for it without reading the text back from the control."""
        self.getControl(EDIT_ID).setText(text)
        self.run_search(text)

    def run_search(self, query):
        self.text = query
        with self.lock:
            if self.search.can_search(query):
                # Set while the current search waits or runs. Older searches finishing later do not clear it.
                self.setProperty(BUSY_PROPERTY, 'true')
                self.search.submit(query, self.show_results)
                return
            self.search.clear()
            self.set_request(EMPTY_REQUEST)

    def research(self):
        """Search again after the sources, sort method or filters change.

        Cached source results are reused so only newly enabled sources and discover sources with new options are
        looked up.
        """
        self.run_search(self.text)

    def select_button(self, button):
        """Show the results of the focused source button. Returning focus to the selected button keeps the list."""
        with self.lock:
            if button is self.selected_button:
                return
            self.set_selected_button(button)
            self.fill_list(self.lists.selected_list)

    def select_source_button(self):
        """Choose a shown source button from a select dialog. Focusing the button shows its results."""
        with self.lock:
            buttons = self.buttons.get_shown_buttons(self.view)
            labels = [get_count_label(button.label, len(button.get_results(self.view))) for button in buttons]
        position = xbmcgui.Dialog().select(
            get_localized(39031),
            labels,
            preselect=buttons.index(self.selected_button),
        )
        if position < 0:
            return
        self.setFocusId(buttons[position].control_id)

    def press_key(self):
        key = KEYBOARD_KEYS[self.getControl(KEYBOARD_ID).getSelectedPosition()]
        self.set_text(key.apply(self.text))

    def select_sources(self):
        sources = self.search.sources
        positions = xbmcgui.Dialog().multiselect(
            get_localized(39031),
            sources.listitems,
            preselect=sources.enabled_positions,
        )
        if not positions:  # Cancelled, or every source was turned off, which keeps the sources already enabled.
            return
        sources.set_enabled_positions(positions)
        with self.lock:
            self.refresh_view()
        self.research()

    def select_sort(self):
        position = xbmcgui.Dialog().select(
            get_localized(581),
            self.search.sort_labels,
            preselect=self.search.sort_position,
        )
        if position < 0:
            return
        self.search.set_sort_position(position)
        self.set_sort_property()
        with self.lock:
            self.refresh_view()
        self.research()

    def select_filter(self, result_filter):
        """Choose a value for the filter from the results of every source, or Any to clear it."""
        with self.lock:
            options = self.view.get_filter_options(result_filter)
            labels = options.labels
        position = xbmcgui.Dialog().select(
            get_localized(result_filter.localized_id),
            labels,
            preselect=options.values.index(result_filter.value) + 1 if result_filter.value else 0,
        )
        if position < 0:
            return
        with self.lock:
            result_filter.set_value(options.values[position - 1] if position else '')
            self.set_properties(result_filter.properties)
            self.refresh_view()
        self.research()

    def toggle_filter(self, result_filter):
        """Switch the filter on or off."""
        with self.lock:
            result_filter.toggle()
            self.set_properties(result_filter.properties)
            self.refresh_view()
        self.research()

    def reset_options(self):
        """Clear the search text, return the filters to their defaults and enable every source.

        Clearing the text empties the results unless a discover source is enabled, which discovers without text.
        """
        with self.lock:
            self.search.reset()
            self.set_properties(self.search.filters.properties)
            self.controls[SOURCES_ID].set_properties(self)
        self.set_text('')

    def get_selected_result(self, control_id):
        """Result selected in the container, from the list that fills it."""
        with self.lock:
            return self.lists.get(control_id).results[self.getControl(control_id).getSelectedPosition()]

    def open_result(self, control_id):
        self.opened_list = self.lists.get(control_id)
        self.opened_position = self.getControl(control_id).getSelectedPosition()
        xbmc.executebuiltin(self.get_selected_result(control_id).builtin)

    def show_info(self, control_id):
        try:
            result = self.get_selected_result(control_id)
        except (IndexError, KeyError):  # Focus can stay on a results list emptied by a new search or another style.
            return
        xbmcgui.Dialog().info(result.listitem)

    def stop(self):
        """Store the search text for the session, drop the queued search and wait for the running searches."""
        self.stored_query.set_value(self.text)
        self.search.close()
