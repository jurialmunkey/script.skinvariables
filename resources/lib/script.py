# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sys
from importlib import import_module


def importmodule(module_name, import_attr=None):
    module = import_module(module_name)
    if not import_attr:
        return module
    return getattr(module, import_attr)


class Script(object):
    def __init__(self):
        def map_args(arg):
            if '=' in arg:
                key, value = arg.split('=', 1)
                value = value.strip('\'').strip('"') if value else None
                return (key, value)
            return (arg, True)

        self.params = {}
        for arg in sys.argv[1:]:
            k, v = map_args(arg)
            self.params[k] = v

    # lambda **kwargs: importmodule('resources.lib.script.method', 'split_value')(**kwargs),
    routing_table = {
        'set_player_subtitle':
            lambda **kwargs: importmodule('resources.lib.method', 'set_player_subtitle')(**kwargs),
        'set_player_audiostream':
            lambda **kwargs: importmodule('resources.lib.method', 'set_player_audiostream')(**kwargs),
        'set_editcontrol':
            lambda **kwargs: importmodule('resources.lib.method', 'set_editcontrol')(**kwargs),
    }

    def run(self):
        if not self.params:
            return
        routes_available, params_given = set(self.routing_table.keys()), set(self.params.keys())
        try:
            route_taken = set.intersection(routes_available, params_given).pop()
        except KeyError:
            return self.router()
        return self.routing_table[route_taken](**self.params)

    def router(self):
        if self.params.get('action') == 'buildviews':
            from resources.lib.viewtypes import ViewTypes
            return ViewTypes().update_xml(skinfolder=self.params.get('folder'), **self.params)
        else:
            from resources.lib.skinvariables import SkinVariables
            return SkinVariables(self.params).update_xml(skinfolder=self.params.get('folder'), **self.params)
