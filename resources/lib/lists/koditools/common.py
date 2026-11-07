# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from functools import wraps
from jurialmunkey.window import set_to_windowprop, clear_windowprops


class WindowProperties:
    keys_property = 'PropertiesList'

    def __init__(self, prefix, window_id=None):
        self.prefix = prefix
        self.window_id = window_id

    def clear(self):
        clear_windowprops(window_prop=self.prefix, window_id=self.window_id, keys_prop=self.keys_property)

    def set(self, key, value):
        set_to_windowprop(value, key, self.prefix, self.window_id)

    def set_values(self, values):
        for key, value in values.items():
            self.set(key, value)

    def store_keys(self, keys):
        self.set(self.keys_property, '||'.join(keys))

    def store_count(self, count):
        self.store_keys(str(index) for index in range(count))

    def write(self, values):
        self.set_values(values)
        self.store_keys(values)


def clear_windowprops_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        WindowProperties(kwargs.get('window_prop'), kwargs.get('window_id')).clear()
        return func(*args, **kwargs)
    return wrapper
