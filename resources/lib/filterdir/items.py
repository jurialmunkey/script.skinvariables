# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from collections import Counter
from jurialmunkey.ftools import cached_property
from jurialmunkey.jsnrpc import get_directory
from jurialmunkey.thread import ParallelThread as BaseParallelThread
from resources.lib.filters import get_filters, is_excluded
from resources.lib.filterdir.jsonrpc import ListItemJSONRPC, get_directory_properties
from resources.lib.kodiutils import kodi_log


class ParallelThread(BaseParallelThread):
    thread_max = 50

    @staticmethod
    def kodi_log(msg, level=0):
        kodi_log(msg, level)


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

    @staticmethod
    def get_filter_data(item):
        return {'infolabels': item.infolabels, 'infoproperties': item.infoproperties}

    def get_item(self, meta, path_name=''):
        if not meta:
            return
        item = ListItemJSONRPC(meta, library=self.library, dbtype=self.dbtype)
        item.infolabels['title'] = item.meta.title
        item.infoproperties['widget'] = path_name or item.infoproperties.get('widget') or ''
        data = self.get_filter_data(item)
        if any(is_excluded(data, **filters) for filters in self.filters.values()):
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
        items = {}
        for item in self.filtered_items:
            items.setdefault(item.infolabels['title'], item)
        return list(items.values())

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
        counts = {
            name: sum(
                not is_excluded(self.get_filter_data(item), **filters)
                for item in self.filtered_items
            )
            for name, filters in self.statistics_filters.items()
        }
        return {name: count for name, count in counts.items() if count}

    @cached_property
    def container_content(self):
        return self.get_container_content()

    def get_container_content(self):
        mediatypes = Counter(item.mediatype for item in self.filtered_items if item.mediatype)
        return f'{max(mediatypes, key=mediatypes.get)}s' if mediatypes else ''
