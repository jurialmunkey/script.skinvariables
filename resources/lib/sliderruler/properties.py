# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property


class SliderRulerProperties:
    """Window property values that draw a ruler scale: the fill and nib of each step and the value label"""

    def __init__(self, scale):
        self.scale = scale

    @cached_property
    def steps(self):
        return self.get_steps()

    def get_steps(self):
        return {
            key: value
            for index in self.scale.indices
            for key, value in (
                (f'{index}.Fill', self.scale.get_fill(index)),
                (f'{index}.Nib', self.scale.get_nib(index)),
            )
        }

    @cached_property
    def values(self):
        return self.get_values()

    def get_values(self):
        return {**self.steps, 'Label': self.scale.label}

    def get_changes(self, previous):
        return {key: value for key, value in self.values.items() if previous.get(key) != value}
