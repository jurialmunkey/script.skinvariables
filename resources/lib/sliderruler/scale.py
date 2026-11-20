# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import re
from jurialmunkey.ftools import cached_property


class DelayValue():
    """
    Reads a Kodi delay label in seconds (for example Player.AudioDelay "-0.150 s")
    and labels it in milliseconds with a sign (for example "−150 ms", "0 ms", "+100 ms").
    """
    number_pattern = re.compile(r'[-+−]?\d+(?:[.,]\d+)?')

    def get_number(self, value):
        match = self.number_pattern.search(value or '')
        return float(match[0].replace('−', '-').replace(',', '.')) if match else 0.0

    @staticmethod
    def get_label(number):
        milliseconds = round(number * 1000)
        sign = '+' if milliseconds > 0 else '−' if milliseconds < 0 else ''
        return f'{sign}{abs(milliseconds)} ms'


class SliderRulerScale(DelayValue):
    """
    Positions of a slider value along a ruler of steps from minimum to maximum.
    Values outside the range pin the nib to the nearest end.
    Fill is full, left or right where the fill from origin (default zero) to the nib crosses the step.
    """

    def __init__(self, value='', minimum='-1', maximum='1', steps='80', origin='0'):
        self.value = value
        self.minimum = float(minimum)
        self.maximum = float(maximum)
        self.steps = int(steps)
        self.origin = float(origin)

    @cached_property
    def number(self):
        return self.get_number(self.value)

    @cached_property
    def label(self):
        return self.get_label(self.number)

    def get_position(self, x):
        return max(0, min(self.steps, round((x - self.minimum) / (self.maximum - self.minimum) * self.steps)))

    @cached_property
    def zero(self):
        return self.get_position(self.origin)

    @cached_property
    def nib(self):
        return self.get_position(self.number)

    @cached_property
    def bounds(self):
        return self.get_bounds()

    def get_bounds(self):
        return sorted((self.zero, self.nib))

    def get_fill(self, index):
        lower, upper = self.bounds
        if lower < index < upper:
            return 'full'
        if lower == upper:
            return ''
        if index == lower:
            return 'right'
        if index == upper:
            return 'left'
        return ''

    def get_nib(self, index):
        return 'true' if index == self.nib else ''

    @cached_property
    def indices(self):
        return range(self.steps + 1)
