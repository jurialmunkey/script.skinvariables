# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import threading
from jurialmunkey.ftools import cached_property
from resources.lib.filterdir.items import ParallelThread


class SearchRequest:
    """Looks up the query for each source in its own thread and combines the results with the sort method."""

    def __init__(self, query, sources, sort_method, limit, callback):
        self.query = query
        self.sources = sources
        self.sort_method = sort_method
        self.limit = limit
        self.callback = callback

    def get_source_results(self, source):
        return source.get_results(self.query, self.limit)

    @cached_property
    def source_results(self):
        return self.get_source_results_list()

    def get_source_results_list(self):
        with ParallelThread(self.sources, self.get_source_results) as threads:
            queue = threads.queue
        return queue

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        return self.sort_method(self.source_results).items[:self.limit]

    def run(self):
        # Build the results on the worker so the callback only displays them.
        self.items
        self.callback(self)


class SearchDispatcher:
    """Runs searches on a single worker with a single slot queue.

    A search submitted while the worker is busy waits in the slot and replaces any search already waiting there.
    """

    worker_count = 1

    def __init__(self):
        self.lock = threading.Lock()
        self.active = 0
        self.queued = None
        self.threads = []

    def submit(self, request):
        with self.lock:
            if self.active >= self.worker_count:
                self.queued = request
                return
            self.active += 1
            self.start_worker(request)

    def start_worker(self, request):
        thread = threading.Thread(target=self.work, args=(request,))
        self.threads.append(thread)
        thread.start()

    def take_queued(self):
        """Next waiting search for a worker that finished. The worker stops when the slot is empty."""
        with self.lock:
            request, self.queued = self.queued, None
            if request is None:
                self.active -= 1
            return request

    def work(self, request):
        while request is not None:
            request.run()
            request = self.take_queued()

    def clear(self):
        with self.lock:
            self.queued = None

    def join(self):
        for thread in self.threads:
            thread.join()
