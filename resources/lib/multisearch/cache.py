# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import threading
from jurialmunkey.ftools import cached_property, threaded_cached_property
from jurialmunkey.futils import FileUtils
from jurialmunkey.scache import SimpleCache, TIME_DAYS
from jurialmunkey.tmdate import set_timestamp


ADDON_DATA = 'special://profile/addon_data/script.skinvariables/'
CACHE_FOLDER = 'multisearch'
CACHE_FILENAME = 'multisearch_v2.db'
CACHE_DAYS = 1
RETAIN_DAYS = 30
# Kodi returns this for a lookup with no results and for a lookup that failed.
EMPTY_DIRECTORY = [{}]


class MultiSearchFileUtils(FileUtils):
    addondata = ADDON_DATA


class MultiSearchSimpleCache(SimpleCache):
    """Simple cache database in the addon data of script.skinvariables instead of script.module.jurialmunkey."""

    _fileutils = MultiSearchFileUtils()


class SearchCacheEntry:
    """Stored directory items of a search path with the time they stop being fresh."""

    def __init__(self, data):
        self.data = data

    @cached_property
    def directory(self):
        return self.data['directory']

    @cached_property
    def expires(self):
        return self.data['expires']

    @property
    def is_stale(self):
        """Whether the items are older than the cache days. Stale items are still used while they are refreshed."""
        return self.expires <= set_timestamp(0, True)


class SearchCache:
    """JSON-RPC directory items of each source search path, fresh for a day and kept for longer.

    The items are stored before any filtering. Stale items are still returned and are refreshed in the background
    afterwards. Empty directories are not stored because Kodi returns the same items for a failed lookup, which would
    otherwise hide the source or replace its stale items.
    """

    def __init__(self, folder=CACHE_FOLDER, filename=CACHE_FILENAME, cache_days=CACHE_DAYS, retain_days=RETAIN_DAYS):
        self.folder = folder
        self.filename = filename
        self.cache_days = cache_days
        self.retain_days = retain_days
        self.refreshing = {}
        self.lock = threading.Lock()

    @threaded_cached_property
    def database(self):
        """Created on first use by the lookups so opening the window does not wait for the database."""
        return self.get_database()

    def get_database(self):
        return MultiSearchSimpleCache(folder=self.folder, filename=self.filename)

    @staticmethod
    def get_endpoint(library, path):
        return f'{library}|{path}'

    def get(self, library, path):
        data = self.database.get(self.get_endpoint(library, path))
        if data is None:
            return
        return SearchCacheEntry(data)

    def get_data(self, directory):
        return {
            'expires': set_timestamp(self.cache_days * TIME_DAYS, True),
            'directory': directory,
        }

    def set(self, library, path, directory):
        if directory == EMPTY_DIRECTORY:
            return
        self.database.set(self.get_endpoint(library, path), self.get_data(directory), cache_days=self.retain_days)

    def refresh(self, library, path, lookup):
        """Look up the path again in the background unless it is already being refreshed."""
        endpoint = self.get_endpoint(library, path)
        with self.lock:
            if endpoint in self.refreshing:
                return
            thread = threading.Thread(target=self.work, args=(endpoint, library, path, lookup))
            self.refreshing[endpoint] = thread
            thread.start()

    def work(self, endpoint, library, path, lookup):
        try:
            self.set(library, path, lookup(path))
        finally:
            with self.lock:
                del self.refreshing[endpoint]

    def stop(self):
        """Wait for the refreshes in progress."""
        with self.lock:
            threads = list(self.refreshing.values())
        for thread in threads:
            thread.join()
