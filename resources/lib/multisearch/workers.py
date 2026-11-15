# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import threading
from jurialmunkey.ftools import cached_property
from resources.lib.multisearch.progress import NO_PROGRESS


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
    finishes, so only searches that are no longer current are left incomplete. A source abandoned by its worker for a
    later search still finishes, but its search is no longer current.

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
    """Looks up one source with a running lookup, an abandoned lookup and a single slot queue.

    A search starts straight away when the worker is free. When a lookup is running and none is abandoned, the running
    lookup is abandoned to finish in the background and the search starts straight away. Otherwise the search waits in
    the slot and replaces any search already waiting there. Once the abandoned lookup finishes, the waiting search is
    newer than the running lookup, so the running lookup is abandoned in turn and the waiting search starts. The worker
    never has more than two lookups in progress.

    An abandoned lookup still stores its results, but its search is no longer current so they are not shown.

    The progress counts each search given to the worker. A waiting search that is replaced or cleared is dropped, as is
    a running lookup once it is abandoned.
    """

    def __init__(self, source, progress=NO_PROGRESS):
        self.source = source
        self.progress = progress
        self.lock = threading.Lock()
        self.running = None
        self.abandoned = None
        self.queued = None

    @property
    def can_start(self):
        """Whether the waiting search can start now. Read while holding the lock."""
        return self.queued is not None and self.running is None

    @property
    def can_abandon(self):
        """Whether the running lookup can be abandoned for the waiting search. Read while holding the lock."""
        return self.queued is not None and self.running is not None and self.abandoned is None

    def submit(self, request):
        with self.lock:
            self.track_queued(request)
            self.queued = request
            self.dispatch()

    def track_queued(self, request):
        """Add the new search to the progress, replacing any waiting search. Called while holding the lock."""
        if self.queued is None:
            self.progress.add(self.source, request)
            return
        self.progress.replace(self.source, request)

    def drop_queued(self):
        """Drop the waiting search from the progress. Called while holding the lock."""
        if self.queued is None:
            return
        self.queued = None
        self.progress.drop(self.source)

    def dispatch(self):
        """Start the waiting search, abandoning the running lookup if no other is abandoned. Called holding the lock."""
        if self.can_abandon:
            self.abandon()
        if not self.can_start:
            return
        request, self.queued = self.queued, None
        self.running = threading.Thread(target=self.work, args=(request,))
        self.running.start()

    def abandon(self):
        """Leave the running lookup to finish in the background. Called while holding the lock."""
        self.abandoned, self.running = self.running, None
        self.progress.abandon(self.source)

    def work(self, request):
        try:
            request.get_source_results(self.source)
        finally:
            with self.lock:
                self.finish(threading.current_thread())
                self.dispatch()

    def finish(self, thread):
        """Free the slot of the finished lookup. Only the running lookup counts. Called while holding the lock."""
        if thread is self.abandoned:
            self.abandoned = None
            return
        self.running = None
        self.progress.complete(self.source)

    @property
    def threads(self):
        """Lookups in progress. Read while holding the lock."""
        return [thread for thread in (self.running, self.abandoned) if thread is not None]

    def clear(self):
        with self.lock:
            self.drop_queued()

    def stop(self):
        """Wait for the running and abandoned lookups. Clear the waiting search before stopping."""
        with self.lock:
            threads = self.threads
        for thread in threads:
            thread.join()


class SearchDispatcher:
    """Runs searches with one worker for each source. Each worker abandons or queues searches for its source.

    The workers share the progress of their lookups, which closes once the workers stop.
    """

    def __init__(self, sources, progress=NO_PROGRESS):
        self.sources = sources
        self.progress = progress

    @cached_property
    def workers(self):
        """Worker of each source of the window, including sources that are disabled."""
        return self.get_workers()

    def get_workers(self):
        return {source: SourceWorker(source, self.progress) for source in self.sources.items}

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
        self.progress.close()
