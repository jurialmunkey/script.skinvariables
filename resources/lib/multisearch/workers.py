# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import threading
from jurialmunkey.ftools import cached_property
from resources.lib.filterdir.items import ParallelThread


SEARCH_DELAY = 0.4


class EmptySearchRequest:
    """Stands in for a search while the search text is empty."""

    results_by_source = {}
    busy = ''


EMPTY_REQUEST = EmptySearchRequest()


class SearchSnapshot:
    """Results of the sources of a search that have finished so far, in the order of the search sources."""

    def __init__(self, request, results_by_source):
        self.request = request
        self.results_by_source = results_by_source

    @cached_property
    def complete(self):
        """Whether every source of the search has finished."""
        return self.get_complete()

    def get_complete(self):
        return len(self.results_by_source) == len(self.request.sources)

    @cached_property
    def busy(self):
        """Busy window property value. Set until every source has finished."""
        return self.get_busy()

    def get_busy(self):
        return '' if self.complete else 'true'


class SearchRequest:
    """Looks up the query for each source in its own thread. The results view filters, sorts and limits them.

    Each source sends the callback a snapshot of the finished results as soon as it finishes. The snapshots are sent
    while holding the lock so the callback receives them in order and the complete snapshot is always the last.
    """

    def __init__(self, query, options, sources, callback):
        self.query = query
        self.options = options
        self.sources = sources
        self.callback = callback
        self.finished = {}
        self.lock = threading.Lock()

    @property
    def snapshot(self):
        """Results of the finished sources. Read while holding the lock."""
        return self.get_snapshot()

    def get_snapshot(self):
        results_by_source = {
            source: self.finished[source]
            for source in self.sources
            if source in self.finished
        }
        return SearchSnapshot(self, results_by_source)

    def get_source_results(self, source):
        # Look up the results before taking the lock so the sources look up in parallel.
        results = source.get_results(self.query, self.options)
        with self.lock:
            self.finished[source] = results
            self.callback(self.snapshot)

    def run(self):
        with ParallelThread(self.sources, self.get_source_results):
            pass


class IdleTimer:
    """Calls the callback once the delay passes without another restart."""

    def __init__(self, callback, delay=SEARCH_DELAY):
        self.callback = callback
        self.delay = delay
        self.timer = self.get_timer()

    def get_timer(self):
        return threading.Timer(self.delay, self.callback)

    @property
    def pending(self):
        """Whether the delay is still running. The callback sees the delay as passed."""
        return self.timer.is_alive() and self.timer is not threading.current_thread()

    def restart(self):
        self.cancel()
        self.timer = self.get_timer()
        self.timer.start()

    def extend(self):
        """Restart the delay only while it is already running."""
        if self.pending:
            self.restart()

    def cancel(self):
        self.timer.cancel()

    def stop(self):
        """Cancel the delay and let a callback that already started finish."""
        self.cancel()
        if self.timer.is_alive():
            self.timer.join()


class SearchDispatcher:
    """Runs searches on two workers with a single slot queue.

    Each search waits in the slot and replaces any search already waiting there. The waiting search starts straight
    away when both workers are free. While one worker is busy, it starts on the spare worker once the search text and
    keyboard have been idle for the search delay. While both workers are busy, it waits for a worker to finish.
    """

    worker_count = 2

    def __init__(self, delay=SEARCH_DELAY):
        self.lock = threading.Lock()
        self.active = 0
        self.queued = None
        self.threads = []
        self.timer = IdleTimer(self.dispatch, delay)

    @property
    def can_start(self):
        """Whether the waiting search can start now. Read while holding the lock."""
        return self.get_can_start()

    def get_can_start(self):
        if self.queued is None or self.active >= self.worker_count:
            return False
        return self.active == 0 or not self.timer.pending

    def submit(self, request):
        with self.lock:
            self.queued = request
            self.timer.restart()
        self.dispatch()

    def extend_wait(self):
        """Keyboard movement counts as activity while a search is waiting for the spare worker."""
        self.timer.extend()

    def dispatch(self):
        """Start the waiting search if it can start. Called on submit, after the delay and when a worker finishes."""
        with self.lock:
            if not self.can_start:
                return
            request, self.queued = self.queued, None
            self.active += 1
            self.start_worker(request)

    def start_worker(self, request):
        thread = threading.Thread(target=self.work, args=(request,))
        self.threads = [*(running for running in self.threads if running.is_alive()), thread]
        thread.start()

    def work(self, request):
        request.run()
        with self.lock:
            self.active -= 1
        self.dispatch()

    def clear(self):
        with self.lock:
            self.queued = None

    def stop(self):
        """Stop the delay and wait for the running searches. Clear the waiting search before stopping."""
        self.timer.stop()
        for thread in list(self.threads):
            thread.join()
