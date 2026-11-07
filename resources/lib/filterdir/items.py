# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from collections import Counter
from jurialmunkey.ftools import cached_property
from jurialmunkey.jsnrpc import get_directory
from jurialmunkey.thread import ParallelThread as BaseParallelThread
from resources.lib.filters.parameters import get_filters
from resources.lib.filters.items import is_excluded
from resources.lib.filterdir.jsonrpc.items import ListItemJSONRPC
from resources.lib.filterdir.jsonrpc.properties import get_directory_properties
from resources.lib.kodiutils import kodi_log


class ParallelThread(BaseParallelThread):
    thread_max = 50

    @staticmethod
    def kodi_log(msg, level=0):
        kodi_log(msg, level)


class FilterDirItem(ListItemJSONRPC):
    def __init__(self, meta, path_name='', library=None, dbtype=None):
        super().__init__(meta, library=library, dbtype=dbtype)
        self.infolabels['title'] = self.meta.title
        self.infoproperties['widget'] = path_name or self.infoproperties.get('widget') or ''
        # Infotagger consumes resume properties during rendering; filtering uses the original metadata.
        self.filter_infolabels = dict(self.infolabels)
        self.filter_infoproperties = dict(self.infoproperties)

    @cached_property
    def filter_data(self):
        return self.get_filter_data()

    def get_filter_data(self):
        return {'infolabels': self.filter_infolabels, 'infoproperties': self.filter_infoproperties}


class FilterDirItems:
    """Build and cache directory results for one configured source."""

    def __init__(
        self,
        paths,
        library=None,
        dbtype=None,
        no_label_dupes=False,
        sort_by=None,
        sort_how=None,
        **kwargs,
    ):
        self.paths = paths
        self.library = library
        self.dbtype = dbtype
        self.no_label_dupes = no_label_dupes
        self.sort_by = sort_by
        self.sort_how = sort_how
        self.filters = get_filters(**kwargs)
        self.statistics_filters = get_filters(filter_prefix='stats_', **kwargs)

    @cached_property
    def directory_properties(self):
        return self.get_directory_properties()

    def get_directory_properties(self):
        return get_directory_properties(self.library)

    def get_item(self, meta, path_name=''):
        if not meta:
            return
        item = FilterDirItem(meta, path_name, library=self.library, dbtype=self.dbtype)
        if any(is_excluded(item.filter_data, **filters) for filters in self.filters.values()):
            return
        return item

    def get_path_items(self, path, name):
        directory = get_directory(path, self.directory_properties)
        with ParallelThread(directory, self.get_item, name) as threads:
            queue = threads.queue
        return [item for item in queue if item]

    @cached_property
    def filtered_items(self):
        return self.get_filtered_items()

    def get_filtered_items(self):
        items = []
        for path, name in self.paths:
            items.extend(self.get_path_items(path, name))
            if items and self.paths.stop_after_items:
                break
        return items

    def get_sort_value(self, item):
        value = item.infolabels.get(self.sort_by) or item.infoproperties.get(self.sort_by) or ''
        try:
            return (2, float(value))
        except ValueError:
            return (1, str(value))
        except TypeError:
            return (0, '')

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        items = self.filtered_items
        if self.no_label_dupes:
            items = self.get_unique_items()
        if self.sort_by:
            items = sorted(items, key=self.get_sort_value, reverse=self.sort_how == 'desc')
        return items

    def get_unique_items(self):
        unique_items = {}
        for item in self.filtered_items:
            unique_items.setdefault(item.infolabels['title'], item)
        return list(unique_items.values())

    @cached_property
    def directory_items(self):
        return self.get_directory_items()

    def get_directory_items(self):
        return [(item.path, item.listitem, item.is_folder) for item in self.items]

    @cached_property
    def statistics(self):
        return self.get_statistics()

    def get_statistics(self):
        # Count accepted items before deduplication, matching the directory's statistics contract.
        counts = {name: self.get_statistic_count(filters) for name, filters in self.statistics_filters.items()}
        return {name: count for name, count in counts.items() if count}

    def get_statistic_count(self, filters):
        return sum(not is_excluded(item.filter_data, **filters) for item in self.filtered_items)

    @cached_property
    def mediatypes(self):
        return self.get_mediatypes()

    def get_mediatypes(self):
        return Counter(item.mediatype for item in self.filtered_items if item.mediatype)

    @cached_property
    def container_content(self):
        return self.get_container_content()

    def get_container_content(self):
        return f'{max(self.mediatypes, key=self.mediatypes.get)}s' if self.mediatypes else ''
