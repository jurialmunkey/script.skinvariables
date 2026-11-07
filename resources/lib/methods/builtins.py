# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from json import loads, JSONDecodeError
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import load_filecontent
from jurialmunkey.parser import boolean
from resources.lib.methods.controls import set_animation_list
from resources.lib.operations import RuleOperations


class RuleBuiltinActions:
    def __init__(self, filepath, params):
        self.filepath = filepath
        self.params = params

    @cached_property
    def meta(self):
        return self.get_meta()

    def get_meta(self):
        try:
            return loads(str(load_filecontent(self.filepath)))
        except (OSError, JSONDecodeError) as error:
            raise Exception(f'Unable to load {self.filepath} !') from error

    @cached_property
    def operations(self):
        return self.get_operations()

    def get_operations(self):
        return RuleOperations(self.meta, **self.params)

    @cached_property
    def actions(self):
        return self.get_actions()

    def get_actions(self):
        return self.operations.get_actions_list(self.operations.meta['actions'])


class BuiltinCallback:
    def __init__(self, template, index, values, params):
        self.template = template
        self.index = index
        self.values = values
        self.params = params

    @cached_property
    def selected_template(self):
        return self.get_selected_template()

    def get_selected_template(self):
        if isinstance(self.index, int):
            return self.params.get(f'executebuiltin_{self.index}') or self.template
        return self.template

    @cached_property
    def value(self):
        return self.get_value()

    def get_value(self):
        if isinstance(self.index, int) and self.values:
            return self.values[self.index]
        return self.index

    @cached_property
    def actions(self):
        return self.get_actions()

    def get_actions(self):
        value = self.value
        if not self.selected_template:
            return []
        return [action.format(x=self.index, v=value) for action in self.selected_template.split('||')]

    def run(self):
        if self.index == -1 or self.index is False:
            return
        run_executebuiltin_list(self.actions)


def run_executebuiltin_list(builtins):
    for builtin in builtins:
        if builtin.startswith('sleep='):
            xbmc.Monitor().waitForAbort(float(builtin[6:]))
            continue
        if builtin.startswith('route='):
            from resources.lib.script import Script
            Script(paramstring=builtin[6:]).run()
            continue
        if builtin.startswith('animation='):
            control_id, event, effect = builtin[10:].split('|')
            set_animation_list([(control_id, event, effect)])
            continue
        xbmc.executebuiltin(builtin)


def run_executebuiltin(run_executebuiltin=None, use_rules=False, **kwargs):
    if not run_executebuiltin:
        return
    if boolean(use_rules):
        actions = RuleBuiltinActions(run_executebuiltin, kwargs).actions
    else:
        actions = run_executebuiltin.split('||')
    return run_executebuiltin_list(actions)


def executebuiltin(executebuiltin='', index=None, values=None, **kwargs):
    BuiltinCallback(executebuiltin, index, values, kwargs).run()
