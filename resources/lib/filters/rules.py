# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import operator
from jurialmunkey.ftools import cached_property
from jurialmunkey.parser import split_items, boolean


class FilterRule:
    def __init__(self, metadata, key, value, operator_type=None):
        self.metadata = metadata
        self.key = key
        self.value = value
        self.operator_type = operator_type

    @cached_property
    def active(self):
        return self.get_active()

    def get_active(self):
        return bool(self.key and self.value)

    @cached_property
    def values(self):
        return self.get_values()

    def get_values(self):
        return split_items(self.value)

    @cached_property
    def comparison(self):
        return self.get_comparison()

    def get_comparison(self):
        return getattr(operator, self.operator_type or 'contains')

    def get_matches(self, meta, value):
        comparison = self.comparison
        return bool(value and comparison(str(meta[self.key]).lower(), str(value).lower()))

    @cached_property
    def excluded(self):
        return self.get_excluded()

    def get_excluded(self):
        return self.active and self.get_values_excluded()

    def get_values_excluded(self):
        raise NotImplementedError


class IncludeValue:
    """Keep a complete match distinct from an allowed empty-field fallback."""

    def __init__(self, rule, value):
        self.rule = rule
        self.value = value

    @cached_property
    def first_failure(self):
        return self.get_first_failure()

    def get_first_failure(self):
        return next(
            (
                meta
                for meta in self.rule.metadata
                if self.rule.key in meta and not self.rule.get_matches(meta, self.value)
            ),
            None,
        )

    @cached_property
    def matched(self):
        return self.get_matched()

    def get_matched(self):
        if self.first_failure is not None:
            return False
        return self.rule.allow_empty or any(self.rule.key in meta for meta in self.rule.metadata)

    @cached_property
    def excluded(self):
        return self.get_excluded()

    def get_excluded(self):
        if self.first_failure is None:
            return not self.matched
        return not (self.rule.allow_empty and self.first_failure.get(self.rule.key) in (None, ''))


class IncludeRule(FilterRule):
    def __init__(self, metadata, key, value, operator_type=None, allow_empty=None):
        super().__init__(metadata, key, value, operator_type)
        self.empty_option = allow_empty

    @cached_property
    def allow_empty(self):
        return self.get_allow_empty()

    def get_allow_empty(self):
        return boolean(self.empty_option)

    def get_values_excluded(self):
        excluded = True
        for value in self.values:
            result = IncludeValue(self, value)
            excluded = result.excluded
            if result.matched:
                break
        return excluded


class ExcludeRule(FilterRule):
    def get_values_excluded(self):
        return any(
            self.get_matches(meta, value)
            for value in self.values
            for meta in self.metadata
            if self.key in meta
        )
