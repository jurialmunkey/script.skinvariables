# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import threading
from jurialmunkey.ftools import cached_property
from resources.lib.filterdir.items import ParallelThread


SEARCH_DELAY = 0.4


class EmptySearchRequest:
    """Stands in for a search while the search text is empty."""

    source_results = []
    results_by_source = {}


EMPTY_REQUEST = EmptySearchRequest()


class SearchRequest:
    """Looks up the query for each source in its own thread. The results view filters, sorts and limits them."""

    def __init__(self, query, options, sources, callback):
        self.query = query
        self.options = options
        self.sources = sources
        self.callback = callback

    def get_source_results(self, source):
        return source.get_results(self.query, self.options)

    @cached_property
    def source_results(self):
        return self.get_source_results_list()

    def get_source_results_list(self):
        with ParallelThread(self.sources, self.get_source_results) as threads:
            queue = threads.queue
        return queue

    @cached_property
    def results_by_source(self):
        return self.get_results_by_source()

    def get_results_by_source(self):
        return dict(zip(self.sources, self.source_results))

    def run(self):
        # Look up the results on the worker so the callback only displays them.
        self.results_by_source
        self.callback(self)


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
