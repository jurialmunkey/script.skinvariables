# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html


SOURCE_LIST_ID = 200


class SourceList:
    """List of the window filled with an item for each shown source button. The selected item decides which results
    the selected results list shows.

    Kodi lists cannot hide single items, so the list is filled again with the shown buttons whenever they change and
    the selected button is selected again at its new position.
    """

    control_id = SOURCE_LIST_ID

    def __init__(self, buttons):
        self.buttons = buttons
        # Buttons the list is filled with, in list order.
        self.items = []

    def clear(self):
        """Forget the filled items. Kodi reloads the window controls when returning from a window opened from it."""
        self.items = []

    def get_selected_position(self, window):
        """Position of the selected item. Below zero while the list is empty, as when Kodi focuses the list before
        onInit fills it.
        """
        return window.getControl(self.control_id).getSelectedPosition()

    def select(self, window, button):
        window.getControl(self.control_id).selectItem(self.items.index(button))

    def fill(self, window, view, selected_button):
        """Fill the list again when the shown buttons change. The selected button is selected even when they do not."""
        self.refill(window, self.buttons.get_shown_buttons(view))
        self.select(window, selected_button)

    def refill(self, window, items):
        if items == self.items:
            return
        self.items = items
        control = window.getControl(self.control_id)
        control.reset()
        control.addItems([button.listitem for button in items])


class NoSourceList(SourceList):
    """Stands in for the source list when the window has no source list or only shows the all sources button."""

    def fill(self, window, view, selected_button):
        pass
