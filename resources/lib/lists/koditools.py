# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.window import set_to_windowprop, clear_windowprops
from jurialmunkey.litems import Container


KEYS_PROP = 'PropertiesList'


def store_windowprops(values, window_prop, window_id=None):
    set_to_windowprop(f'{"||".join(values)}', KEYS_PROP, window_prop, window_id)


def store_windowprops_counter(stop, window_prop, window_id=None):
    store_windowprops([str(x) for x in range(0, stop)], window_prop, window_id)


def clear_windowprops_decorator(func):
    def wrapper(*args, **kwargs):
        clear_windowprops(window_prop=kwargs.get('window_prop'), window_id=kwargs.get('window_id'), keys_prop=KEYS_PROP)
        return func(*args, **kwargs)
    return wrapper


class ListGetNumberSum(Container):

    @clear_windowprops_decorator
    def get_directory(self, expression, window_prop=None, window_id=None, **kwargs):

        values = [0]
        values += [int(i) for i in expression.split() if i]

        label = f'{sum(values)}'
        items = [self.get_list_item(label)]
        set_to_windowprop(label, 0, window_prop, window_id)

        self.add_items(items)


class ListRunExecuteBuiltin(Container):
    def get_directory(self, paths, **kwargs):
        from resources.lib.method import run_executebuiltin

        for path in paths:
            run_executebuiltin(path, use_rules=True, **kwargs)

        items = [self.get_list_item('None')]  # Add a blank item to keep container alive

        self.add_items(items)


class ListGetJSONRPC(Container):

    @clear_windowprops_decorator
    def get_directory(self, info, method, window_prop=None, window_id=None, **kwargs):
        from jurialmunkey.jsnrpc import get_jsonrpc
        result = get_jsonrpc(method, kwargs) or {}
        result = result.get("result")
        if not result:
            return

        items = [self.get_list_item(method)]

        li = items[0][1]
        keys = []
        for k, v in result.items():
            li.setProperty(str(k), str(v))
            set_to_windowprop(v, k, window_prop, window_id)
            keys.append(k)

        store_windowprops(keys, window_prop, window_id)
        self.add_items(items)

        return result


class ListGetSplitString(Container):

    @clear_windowprops_decorator
    def get_directory(self, values=None, infolabel=None, separator='|', window_prop=None, window_id=None, **kwargs):
        from xbmc import getInfoLabel as get_infolabel
        values = get_infolabel(infolabel) if infolabel else values

        if not values:
            return

        x = 0
        items = []
        for i in values.split(separator):
            if not i:
                continue
            label = f'{i}'
            items.append(self.get_list_item(label))
            set_to_windowprop(label, x, window_prop, window_id)
            x += 1

        store_windowprops_counter(x, window_prop, window_id)
        self.add_items(items)


class ListGetEncodedString(Container):

    @clear_windowprops_decorator
    def get_directory(self, paths=None, window_prop=None, window_id=None, **kwargs):
        from urllib.parse import quote_plus

        if not paths:
            return

        items = []
        for x, i in enumerate(paths):
            label = quote_plus(i)
            items.append(self.get_list_item(label))
            set_to_windowprop(label, x, window_prop, window_id)

        store_windowprops_counter(x + 1, window_prop, window_id)
        self.add_items(items)


class ListGetFileExists(Container):

    @clear_windowprops_decorator
    def get_directory(self, paths, window_prop=None, window_id=None, **kwargs):
        import xbmcvfs

        if not paths:
            return

        items = []
        for x, i in enumerate(paths):
            label = i
            path = i if xbmcvfs.exists(i) else ''
            items.append(self.get_list_item(label))
            set_to_windowprop(path, x, window_prop, window_id)

        store_windowprops_counter(x + 1, window_prop, window_id)
        self.add_items(items)


class ListGetSelectedItem(Container):
    def get_directory(
            self, container, infolabels='', artwork='', separator='/', listitem='ListItem(0)',
            window_prop=None, window_id=None, **kwargs
    ):
        import xbmc

        if not container:
            return

        _fstr = f'Container({container}).{listitem}.{{}}'
        _label = xbmc.getInfoLabel(_fstr.format('Label'))

        _infoproperties = {}
        for i in infolabels.split(separator):
            _infoproperties[i] = xbmc.getInfoLabel(_fstr.format(i))

        _artwork = {}
        for i in artwork.split(separator):
            _artwork[i] = xbmc.getInfoLabel(_fstr.format(f'Art({i})'))

        item = self.get_list_item(_label)
        item[1].setProperties(_infoproperties)
        item[1].setArt(_artwork)

        self.add_items([item])

        if not window_prop:
            return

        window_id = f',{window_id}' if window_id else ''

        for k, v in _infoproperties.items():
            window_prop_name = f'{window_prop}.{k}'
            xbmc.executebuiltin(f'SetProperty({window_prop_name},{v}{window_id})')

        for k, v in _artwork.items():
            window_prop_name = f'{window_prop}.{k}'
            xbmc.executebuiltin(f'SetProperty({window_prop_name},{v}{window_id})')
