# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import threaded_cached_property
from jurialmunkey.futils import FileUtils
from jurialmunkey.scache import SimpleCache


ADDON_DATA = 'special://profile/addon_data/script.skinvariables/'
CACHE_FOLDER = 'multisearch'
CACHE_FILENAME = 'multisearch.db'
CACHE_DAYS = 1
# Kodi returns this for a lookup with no results and for a lookup that failed.
EMPTY_DIRECTORY = [{}]


class MultiSearchFileUtils(FileUtils):
    addondata = ADDON_DATA


class MultiSearchSimpleCache(SimpleCache):
    """Simple cache database in the addon data of script.skinvariables instead of script.module.jurialmunkey."""

    _fileutils = MultiSearchFileUtils()


class SearchCache:
    """JSON-RPC directory items of each source search path, kept for a day.

    The items are stored before any filtering. Empty directories are not stored because Kodi returns the same items
    for a failed lookup, which would otherwise hide the source for a day.
    """

    def __init__(self, folder=CACHE_FOLDER, filename=CACHE_FILENAME, cache_days=CACHE_DAYS):
        self.folder = folder
        self.filename = filename
        self.cache_days = cache_days

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
        return self.database.get(self.get_endpoint(library, path))

    def set(self, library, path, directory):
        if directory == EMPTY_DIRECTORY:
            return
        self.database.set(self.get_endpoint(library, path), directory, cache_days=self.cache_days)
