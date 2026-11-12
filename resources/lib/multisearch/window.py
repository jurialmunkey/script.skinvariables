# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import threading
import xbmc
import xbmcgui
from jurialmunkey.ftools import cached_property
from resources.lib.kodiutils import get_localized
from resources.lib.multisearch.constants import PROPERTY_PREFIX
from resources.lib.multisearch.keyboard import KEYBOARD_KEYS
from resources.lib.multisearch.workers import EMPTY_REQUEST
from resources.lib.scriptwindow.window import ScriptWindow


RESULTS_ID = 50
EDIT_ID = 100
KEYBOARD_ID = 101
SOURCES_ID = 102
SORT_ID = 103
SORT_PROPERTY = f'{PROPERTY_PREFIX}.SortBy'
COUNT_PROPERTY = f'{PROPERTY_PREFIX}.Count'


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
        # Edit controls send a click each time their text changes.
        window.run_search()


class KeyboardControl(MultiSearchControl):
    control_id = KEYBOARD_ID

    def onclick(self, window):
        window.press_key()


class SourcesButton(MultiSearchControl):
    control_id = SOURCES_ID

    def onclick(self, window):
        window.select_sources()


class SortButton(MultiSearchControl):
    control_id = SORT_ID

    def onclick(self, window):
        window.select_sort()


class ResultsControl(MultiSearchControl):
    control_id = RESULTS_ID

    def onclick(self, window):
        window.open_result()

    def onaction(self, window, action_id):
        # Python windows skip the media window actions so Kodi does not open the info dialog itself.
        if action_id == xbmcgui.ACTION_SHOW_INFO:
            window.show_info()


UNFOCUSED_CONTROL = MultiSearchControl()
MULTISEARCH_CONTROLS = {
    control.control_id: control
    for control in (
        SearchEditControl(),
        KeyboardControl(),
        SourcesButton(),
        SortButton(),
        ResultsControl(),
    )
}


class MultiSearchWindow(ScriptWindow):
    """Searches the enabled sources each time the search text changes and lists the combined results.

    Results arrive from the search worker so changes to the results list are made while holding the lock.
    The focused source button decides whether the list shows the results of all sources or of one source.
    """

    def __init__(self, *args, search=None, buttons=None, **kwargs):
        self.search = search
        self.buttons = buttons
        self.request = EMPTY_REQUEST
        self.selected_button = buttons.all_button
        self.results = []
        self.lock = threading.Lock()

    @cached_property
    def controls(self):
        return {**MULTISEARCH_CONTROLS, **self.buttons.controls}

    @property
    def query(self):
        return self.getControl(EDIT_ID).getText()

    def onInit(self):
        # Kodi calls onInit again when returning from a window opened from the results.
        self.fill_keyboard()
        self.set_sort_property()
        self.set_properties(self.buttons.enabled_properties)
        self.set_properties(self.selected_button.focus_properties)
        with self.lock:
            self.fill_results()

    def onAction(self, action):
        self.controls.get(self.getFocusId(), UNFOCUSED_CONTROL).onaction(self, action.getId())
        super().onAction(action)

    def fill_keyboard(self):
        control = self.getControl(KEYBOARD_ID)
        control.reset()
        control.addItems([key.listitem for key in KEYBOARD_KEYS])

    def set_sort_property(self):
        self.setProperty(SORT_PROPERTY, self.search.sort_method.get_label())

    def fill_results(self):
        self.results = self.selected_button.get_results(self.request)
        control = self.getControl(RESULTS_ID)
        control.reset()
        control.addItems([result.listitem for result in self.results])
        self.setProperty(COUNT_PROPERTY, str(len(self.results)))

    def set_request(self, request):
        self.request = request
        self.fill_results()

    def show_results(self, request):
        """Called by the search worker. Results of searches replaced by a later search are discarded."""
        with self.lock:
            if not self.search.is_current(request):
                return
            self.set_request(request)

    def run_search(self):
        query = self.query
        with self.lock:
            if query.strip():
                self.search.submit(query, self.show_results)
                return
            self.search.clear()
            self.set_request(EMPTY_REQUEST)

    def select_button(self, button):
        """Show the results of the focused source button. Returning focus to the selected button keeps the list."""
        self.set_properties(button.focus_properties)
        with self.lock:
            if button is self.selected_button:
                return
            self.selected_button = button
            self.fill_results()

    def press_key(self):
        key = KEYBOARD_KEYS[self.getControl(KEYBOARD_ID).getSelectedPosition()]
        self.getControl(EDIT_ID).setText(key.apply(self.query))
        self.run_search()

    def select_sources(self):
        sources = self.search.sources
        positions = xbmcgui.Dialog().multiselect(
            get_localized(39031),
            sources.listitems,
            preselect=sources.enabled_positions,
            useDetails=True,
        )
        if positions is None:
            return
        sources.set_enabled_positions(positions)
        self.set_properties(self.buttons.enabled_properties)
        if not self.selected_button.is_enabled(sources):
            self.select_button(self.buttons.all_button)
        # Cached source results are reused so only newly enabled sources are looked up.
        self.run_search()

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
        self.run_search()

    @property
    def selected_result(self):
        with self.lock:
            return self.results[self.getControl(RESULTS_ID).getSelectedPosition()]

    def open_result(self):
        xbmc.executebuiltin(self.selected_result.builtin)

    def show_info(self):
        try:
            result = self.selected_result
        except IndexError:  # Focus can stay on the emptied results list after the search text is cleared.
            return
        xbmcgui.Dialog().info(result.listitem)

    def stop(self):
        """Drop the queued search and wait for the running search once the window has closed."""
        self.search.close()
