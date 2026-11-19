# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import re
from jurialmunkey.ftools import cached_property
from jurialmunkey.litems import ContainerDirectory
from resources.lib.methods.builtins import RuleBuiltinActions, run_executebuiltin_list
from resources.lib.shortcuts.node.constants import SKIN_DIR


class InfoLabelKey:
    pattern = re.compile(r'^(\w+)\((.+)\)$')

    def __init__(self, name):
        self.name = name

    @cached_property
    def match(self):
        return self.get_match()

    def get_match(self):
        return self.pattern.match(self.name)

    @cached_property
    def key(self):
        return self.get_key()

    def get_key(self):
        key = f'{self.match[1]}_{self.match[2]}' if self.match else self.name
        return key.replace('.', '_').lower()


class ScriptArguments:
    def __init__(self, items, params):
        self.items = items
        self.params = params

    @staticmethod
    def get_item_arguments(values, prefix=''):
        return {f'{prefix}{InfoLabelKey(name).key}': str(value) for name, value in values.items()}

    @cached_property
    def first_item(self):
        return self.get_first_item()

    def get_first_item(self):
        return self.get_item_arguments(self.items[0]) if self.items else {}

    @cached_property
    def listitems(self):
        return self.get_listitems()

    def get_listitems(self):
        return {
            key: value
            for index, values in enumerate(self.items)
            for key, value in self.get_item_arguments(values, f'listitem_{index}_').items()
        }

    @staticmethod
    def get_param_arguments(key, value):
        if isinstance(value, list):
            return {f'param_{key}_{index}': str(item) for index, item in enumerate(value)}
        return {f'param_{key}': str(value)}

    @cached_property
    def param_arguments(self):
        return self.get_params()

    def get_params(self):
        return {
            name: item
            for key, value in self.params.items()
            for name, item in self.get_param_arguments(key, value).items()
        }

    @cached_property
    def arguments(self):
        return self.get_arguments()

    def get_arguments(self):
        return {**self.param_arguments, **self.listitems, **self.first_item, 'count': str(len(self.items))}


class ScriptPath:
    special_prefix = 'special://'

    def __init__(self, filepath):
        self.filepath = filepath

    @cached_property
    def path(self):
        return self.get_path()

    def get_path(self):
        if self.filepath.startswith(self.special_prefix):
            return self.filepath
        if ':' in self.filepath or '\\' in self.filepath:
            raise ValueError(f'Unsupported run_script path {self.filepath} !')
        return f'{SKIN_DIR}{self.filepath.lstrip("/")}'


class ItemScript:
    def __init__(self, filepath, items, params):
        self.filepath = filepath
        self.items = items
        self.params = params

    @cached_property
    def path(self):
        return self.get_path()

    def get_path(self):
        return ScriptPath(self.filepath).path

    @cached_property
    def arguments(self):
        return self.get_arguments()

    def get_arguments(self):
        return ScriptArguments(self.items, self.params).arguments

    @cached_property
    def actions(self):
        return self.get_actions()

    def get_actions(self):
        return RuleBuiltinActions(self.path, self.arguments).actions

    def run(self):
        run_executebuiltin_list(self.actions)


class ScriptContainerDirectory(ContainerDirectory):
    def run_item_script(self, items):
        filepath = self.params.get('run_script')
        if not filepath:
            return
        ItemScript(filepath, items, self.params).run()
