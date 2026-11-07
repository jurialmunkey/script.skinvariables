# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from jurialmunkey.parser import merge_dicts


class ViewTypesDefaults:
    def __init__(self, rules):
        self.rules = rules

    @cached_property
    def library(self):
        return self.get_library()

    def get_library(self):
        return {key: rule.get('library') for key, rule in self.rules.items()}

    @cached_property
    def plugins(self):
        return self.get_plugins()

    def get_plugins(self):
        return {key: rule.get('plugins') or rule.get('library') for key, rule in self.rules.items()}

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        return {'library': self.library, 'plugins': self.plugins}


class ViewTypesPreferences:
    def __init__(self, meta, rules, defaults):
        self.meta = meta
        self.rules = rules
        self.defaults = defaults

    def is_valid_rule(self, contentid, viewid):
        if not contentid or not viewid:
            return False
        try:
            return viewid in self.rules[contentid]['viewtypes']
        except KeyError:
            return False

    def get_valid_rules(self, rules):
        return {contentid: viewid for contentid, viewid in rules.items() if self.is_valid_rule(contentid, viewid)}

    @cached_property
    def validated(self):
        return self.get_validated()

    def get_validated(self):
        return {location: self.get_valid_rules(rules) for location, rules in self.meta.items()}

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        return merge_dicts(self.defaults, self.validated)
