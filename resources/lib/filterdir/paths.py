# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import random
from jurialmunkey.ftools import cached_property
from jurialmunkey.tmdate import get_timestamp, set_timestamp
from jurialmunkey.window import get_property


class FilterDirPaths:
    """Pair paths and names without consuming the caller's configuration."""

    stop_after_items = False

    def __init__(self, paths, names=None):
        self.paths = tuple(paths or ())
        self.names = tuple(names or ())

    @cached_property
    def path_names(self):
        return self.get_path_names()

    def get_path_names(self):
        return tuple(
            (path, self.names[index] if index < len(self.names) else '')
            for index, path in enumerate(self.paths)
        )

    def __iter__(self):
        return iter(self.path_names)


class FallbackFilterDirPaths(FilterDirPaths):
    stop_after_items = True


class RandomFilterDirPaths(FallbackFilterDirPaths):
    property_prefix = 'SkinVariables.RandomisationTimer'

    def __init__(self, paths, names=None, randomise_prop=None, randomise_time=None):
        super().__init__(paths, names)
        self.randomise_prop = randomise_prop
        self.randomise_time = randomise_time

    @cached_property
    def time_limit(self):
        return self.get_time_limit()

    def get_time_limit(self):
        return int(self.randomise_time or 600)

    def get_stored_index(self, total):
        if not self.randomise_prop:
            return
        expiry = get_property(f'{self.randomise_prop}.expiry', prefix=self.property_prefix)
        previous = get_property(self.randomise_prop, prefix=self.property_prefix)
        previous = int(previous) if previous else -1
        if get_timestamp(expiry, set_int=True) and 0 <= previous < total:
            return previous

        index = random.choice([index for index in range(total) if index != previous])
        self.set_stored_index(index)
        return index

    def set_stored_index(self, index):
        get_property(
            f'{self.randomise_prop}.expiry',
            set_property=str(set_timestamp(self.time_limit, set_int=True)),
            prefix=self.property_prefix,
        )
        get_property(self.randomise_prop, set_property=str(index), prefix=self.property_prefix)

    def get_random_index(self, total):
        if total == 1:
            return 0
        index = self.get_stored_index(total)
        return random.randrange(total) if index is None else index

    def __iter__(self):
        remaining = list(self.path_names)
        while remaining:
            yield remaining.pop(self.get_random_index(len(remaining)))
