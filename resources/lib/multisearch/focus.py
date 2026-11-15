# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc


class FocusTarget:
    """Nothing to focus again. The window keeps the focus that Kodi restored."""

    def restore(self, window):
        pass


NO_FOCUS_TARGET = FocusTarget()


class ResultFocusTarget(FocusTarget):
    """Position in a results container that is focused again once the container is shown.

    The skin can hide a container until it is filled, and Kodi only focuses a control it shows. Kodi updates the shown
    controls once per frame, so a focus sent straight after filling the container can be dropped and focus stays on
    the default control. The container is focused once it is shown, until it has focus or the attempts run out.
    """

    attempts = 20
    interval = 0.05

    def __init__(self, control_id, position):
        self.control_id = control_id
        self.position = position

    @property
    def is_shown(self):
        return xbmc.getCondVisibility(f'Control.IsVisible({self.control_id})')

    def is_focused(self, window):
        return window.getFocusId() == self.control_id

    def try_focus(self, window, monitor):
        """Focus the container if it is shown. True once the container has focus or Kodi is closing."""
        if self.is_shown:
            window.setFocusId(self.control_id)
        return monitor.waitForAbort(self.interval) or self.is_focused(window)

    def restore(self, window):
        window.getControl(self.control_id).selectItem(self.position)
        monitor = xbmc.Monitor()
        for _ in range(self.attempts):
            if self.try_focus(window, monitor):
                return


class NoOpenedResult:
    """No result was opened from the lists since the window last returned."""

    @property
    def focus_target(self):
        return NO_FOCUS_TARGET


NO_OPENED_RESULT = NoOpenedResult()


class OpenedResult(NoOpenedResult):
    """Result opened from a results list, which is focused again when the window returns from the window it opened.

    Kodi reloads the window controls when returning so its own focus restore finds the results list empty.
    """

    def __init__(self, results_list, position):
        self.results_list = results_list
        self.position = position

    @property
    def focus_target(self):
        """Position in the refilled list. Read while holding the window lock after the lists are filled again."""
        return self.get_focus_target()

    def get_focus_target(self):
        results = self.results_list.results
        if not results:  # Emptied while results update or while a content type list repeats the list of all results.
            return NO_FOCUS_TARGET
        return ResultFocusTarget(self.results_list.control_id, min(self.position, len(results) - 1))
