# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import threading
from jurialmunkey.ftools import cached_property


BURST_DELAY = 0.15


class EmptySearchRequest:
    """Stands in for a search while the search text is empty."""

    results_by_source = {}
    complete = True
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
    """Search of the query on each of its sources. The source workers look up each source in their own thread.

    The results view filters, sorts and limits them. A source replaced in its worker's queue by a later search never
    finishes, so only searches that are no longer current are left incomplete.

    Sources that finish within the burst delay of each other send the callback one snapshot of the finished results.
    The complete snapshot is sent as soon as the last source finishes. Snapshots are sent while holding the lock and
    only when more sources have finished, so the callback receives them in order and the complete snapshot is last.
    """

    def __init__(self, query, options, sources, callback):
        self.query = query
        self.options = options
        self.sources = sources
        self.callback = callback
        self.finished = {}
        self.sent_count = 0
        self.lock = threading.Lock()
        self.timer = BurstTimer(self.send_waiting_snapshot)

    @property
    def complete(self):
        """Whether every source has finished. Read while holding the lock."""
        return len(self.finished) == len(self.sources)

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
            self.update()

    def update(self):
        """Send the complete snapshot now, otherwise wait for the burst delay. Called while holding the lock."""
        if self.complete:
            self.timer.cancel()
            self.send_snapshot()
            return
        self.timer.trigger()

    def send_snapshot(self):
        """Send the finished results unless they were already sent. Called while holding the lock."""
        if len(self.finished) == self.sent_count:
            return
        self.sent_count = len(self.finished)
        self.callback(self.snapshot)

    def send_waiting_snapshot(self):
        """Called by the burst timer once the delay passes."""
        with self.lock:
            self.timer.release()
            self.send_snapshot()


class BurstTimer:
    """Calls the callback once the delay passes after the first trigger. Later triggers join the waiting call.

    The call waits from the first trigger until the callback releases it. The owner calls trigger and release while
    holding its own lock, so a trigger never joins a call that has already taken the waiting results.
    """

    def __init__(self, callback, delay=BURST_DELAY):
        self.callback = callback
        self.delay = delay
        self.waiting = False
        self.timer = self.get_timer()

    def get_timer(self):
        return threading.Timer(self.delay, self.callback)

    def trigger(self):
        if self.waiting:
            return
        self.waiting = True
        self.timer = self.get_timer()
        self.timer.start()

    def release(self):
        self.waiting = False

    def cancel(self):
        self.timer.cancel()


class SourceWorker:
    """Looks up one source for one search at a time with a single slot queue.

    A search starts straight away when the worker is free. Otherwise it waits in the slot and replaces any search
    already waiting there, so only the latest search runs once the lookup in progress finishes.
    """

    def __init__(self, source):
        self.source = source
        self.lock = threading.Lock()
        self.busy = False
        self.queued = None
        self.thread = None

    @property
    def can_start(self):
        """Whether the waiting search can start now. Read while holding the lock."""
        return self.queued is not None and not self.busy

    def submit(self, request):
        with self.lock:
            self.queued = request
            self.dispatch()

    def dispatch(self):
        """Start the waiting search if the worker is free. Called while holding the lock."""
        if not self.can_start:
            return
        request, self.queued = self.queued, None
        self.busy = True
        self.thread = threading.Thread(target=self.work, args=(request,))
        self.thread.start()

    def work(self, request):
        request.get_source_results(self.source)
        with self.lock:
            self.busy = False
            self.dispatch()

    def clear(self):
        with self.lock:
            self.queued = None

    def stop(self):
        """Wait for the running lookup. Clear the waiting search before stopping."""
        with self.lock:
            thread = self.thread
        if thread is not None:
            thread.join()


class SearchDispatcher:
    """Runs searches with one worker for each source. Each worker has a single slot queue for its source."""

    def __init__(self, sources):
        self.sources = sources

    @cached_property
    def workers(self):
        """Worker of each source of the window, including sources that are disabled."""
        return self.get_workers()

    def get_workers(self):
        return {source: SourceWorker(source) for source in self.sources.items}

    def submit(self, request):
        for source in request.sources:
            self.workers[source].submit(request)

    def clear(self):
        for worker in self.workers.values():
            worker.clear()

    def stop(self):
        """Wait for the running lookups. Clear the waiting searches before stopping."""
        for worker in self.workers.values():
            worker.stop()
