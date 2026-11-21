# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property


class SliderRulerProperties:
    """Window property values that draw a ruler scale: the step indices bounding the fill, the nib and origin steps
    and the label. Each ruler step compares its own index against these in the skin."""

    def __init__(self, scale):
        self.scale = scale

    @cached_property
    def values(self):
        return self.get_values()

    def get_values(self):
        lower, upper = self.scale.bounds
        return {
            'Lower': f'{lower}',
            'Upper': f'{upper}',
            'Nib': f'{self.scale.nib}',
            'Origin': f'{self.scale.zero}',
            'Label': self.scale.label,
        }

    def get_changes(self, previous):
        """Values that differ from the previous values, where missing values are empty as properties start cleared"""
        return {key: value for key, value in self.values.items() if previous.get(key, '') != value}
