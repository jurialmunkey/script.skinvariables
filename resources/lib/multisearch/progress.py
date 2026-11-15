# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import threading
import xbmcgui
from jurialmunkey.ftools import cached_property
from resources.lib.kodiutils import get_localized


START_DELAY = 0.4
GRACE_DELAY = 0.2


class NoSearchProgress:
    """Stands in for the progress dialog when the skin does not pass the progress_dialog param."""

    def add(self, source, request):
        pass

    def replace(self, source, request):
        pass

    def drop(self, source):
        pass

    def abandon(self, source):
        pass

    def complete(self, source):
        pass

    def close(self):
        pass


NO_PROGRESS = NoSearchProgress()


class PendingLookup:
    """Lookup of the source for the search request that has not finished."""

    def __init__(self, source, request):
        self.source = source
        self.request = request

    @property
    def label(self):
        return self.source.label

    @cached_property
    def heading(self):
        return self.get_heading()

    def get_heading(self):
        return get_localized(32104).format(self.request.query.raw)


class ProgressTimer:
    """Calls fire after the delay unless cancelled or started again first.

    The timer acts while holding the lock of the progress. A timer cancelled or replaced after it started waiting does
    nothing when it expires.
    """

    def __init__(self, progress, delay):
        self.progress = progress
        self.delay = delay
        self.timer = None

    @property
    def waiting(self):
        """Whether the timer is waiting to fire. Read while holding the lock."""
        return self.timer is not None

    def start(self):
        """Called while holding the lock."""
        self.cancel()
        self.timer = threading.Timer(self.delay, self.expire)
        self.timer.start()

    def cancel(self):
        """Called while holding the lock."""
        if self.timer is None:
            return
        self.timer.cancel()
        self.timer = None

    def expire(self):
        with self.progress.lock:
            if self.timer is not threading.current_thread():
                return
            self.timer = None
            self.fire()

    def fire(self):
        """Called while holding the lock."""
        raise NotImplementedError


class StartTimer(ProgressTimer):
    """Opens the dialog once lookups have been running for the start delay."""

    def fire(self):
        self.progress.open_dialog()


class CloseTimer(ProgressTimer):
    """Closes the dialog once every lookup has finished for the grace delay."""

    def fire(self):
        self.progress.close_dialog()


class SearchProgress:
    """Background progress dialog of the source lookups that are running or queued.

    The total counts each lookup given to a worker and the value counts each lookup that has finished. Lookups added
    while the dialog shows add to the total. A queued lookup replaced by a later search or cleared never runs, so it is
    dropped from the total. A running lookup abandoned for a later search is dropped from the total too and its
    finish is not counted. The heading names the query and the message is the label of the source of the oldest
    lookup that has not finished. Once every lookup has finished, the dialog keeps the last heading and message.

    The dialog opens once lookups have been running for the start delay, so lookups that all finish sooner show no
    dialog. Once every lookup has finished, the dialog closes after the grace delay unless another lookup is added
    first, so searches in quick succession keep the same dialog. The next lookup after it closes starts a new delay.
    """

    def __init__(self, start_delay=START_DELAY, grace_delay=GRACE_DELAY):
        self.lock = threading.Lock()
        self.dialog = None
        self.total = 0
        self.value = 0
        self.pending = []
        self.start_timer = StartTimer(self, start_delay)
        self.close_timer = CloseTimer(self, grace_delay)

    @property
    def heading(self):
        """Searching heading of the query of the oldest unfinished lookup. Read while holding the lock.

        Empty once every lookup has finished, which leaves the dialog heading unchanged.
        """
        if not self.pending:
            return ''
        return self.pending[0].heading

    @property
    def message(self):
        """Label of the source of the oldest unfinished lookup. Read while holding the lock."""
        if not self.pending:
            return ''
        return self.pending[0].label

    @property
    def percent(self):
        """Percent of the lookups that have finished. Read while holding the lock."""
        if not self.total:
            return 0
        return int(self.value * 100 / self.total)

    @property
    def finished(self):
        """Whether every lookup has finished. Read while holding the lock."""
        return self.value >= self.total

    def add(self, source, request):
        with self.lock:
            self.close_timer.cancel()
            self.total += 1
            self.pending.append(PendingLookup(source, request))
            self.show()

    def replace(self, source, request):
        """Replace the queued lookup of the source with a later one, which becomes the newest pending lookup."""
        with self.lock:
            self.remove_queued(source)
            self.pending.append(PendingLookup(source, request))
            self.update()

    def drop(self, source):
        with self.lock:
            self.total -= 1
            self.remove_queued(source)
            self.update()

    def abandon(self, source):
        """Drop the running lookup of the source, which a later search replaced while it finishes in the background."""
        with self.lock:
            self.total -= 1
            self.remove_running(source)
            self.update()

    def complete(self, source):
        with self.lock:
            self.value += 1
            self.remove_running(source)
            self.update()

    def get_indices(self, source):
        """Indices of the pending lookups of the source, oldest first. Called while holding the lock."""
        return [
            index
            for index, lookup in enumerate(self.pending)
            if lookup.source is source
        ]

    def remove_running(self, source):
        """Remove the oldest pending lookup of the source, its running lookup. Called while holding the lock."""
        del self.pending[self.get_indices(source)[0]]

    def remove_queued(self, source):
        """Remove the newest pending lookup of the source, which is its queued lookup. Called while holding the lock."""
        del self.pending[self.get_indices(source)[-1]]

    def show(self):
        """Update the dialog if it is showing, otherwise wait for the start delay. Called while holding the lock."""
        if self.dialog is not None:
            self.refresh()
            return
        if not self.start_timer.waiting:
            self.start_timer.start()

    def update(self):
        """Update the dialog if it is showing and finish once every lookup has finished. Called holding the lock."""
        if self.dialog is not None:
            self.refresh()
        if self.finished:
            self.finish()

    def refresh(self):
        """Called while holding the lock."""
        self.dialog.update(self.percent, heading=self.heading, message=self.message)

    def finish(self):
        """Close the dialog after the grace delay, or start again if it never opened. Called holding the lock."""
        if self.dialog is None:
            self.reset()
            return
        self.close_timer.start()

    def open_dialog(self):
        """Called while holding the lock."""
        self.dialog = xbmcgui.DialogProgressBG()
        self.dialog.create(self.heading, self.message)
        self.refresh()

    def close_dialog(self):
        """Close the dialog and start the counts again for the next dialog. Called while holding the lock."""
        if self.dialog is not None:
            self.dialog.close()
        self.dialog = None
        self.reset()

    def reset(self):
        """Start the counts again and stop waiting to open the dialog. Called while holding the lock."""
        self.start_timer.cancel()
        self.total = 0
        self.value = 0
        self.pending = []

    def close(self):
        with self.lock:
            self.close_timer.cancel()
            self.close_dialog()
