# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import re
from jurialmunkey.window import get_property
from resources.lib.lists.koditools.common import WindowProperties, clear_windowprops_decorator
from resources.lib.lists.koditools.scripts import ScriptContainerDirectory


class ListGetRefreshCounter(ScriptContainerDirectory):
    @clear_windowprops_decorator
    def get_directory(self, uid, window_prop=None, window_id=None, **kwargs):
        value = int(get_property(uid, prefix='SkinVariables') or 0) + 1
        get_property(uid, prefix='SkinVariables', set_property=str(value))
        label = str(value)
        items = [self.get_list_item(label)]
        WindowProperties(window_prop, window_id).set(0, label)
        self.add_items(items)
        self.run_item_script([{'Label': label}])


class ListGetNumberSum(ScriptContainerDirectory):
    @clear_windowprops_decorator
    def get_directory(self, expression, window_prop=None, window_id=None, **kwargs):
        label = str(sum(int(value) for value in expression.split() if value))
        items = [self.get_list_item(label)]
        WindowProperties(window_prop, window_id).set(0, label)
        self.add_items(items)
        self.run_item_script([{'Label': label}])


class DelayValue():
    """
    Reads a Kodi delay label in seconds (for example Player.AudioDelay "-0.150 s")
    and labels it in milliseconds with a sign (for example "−150 ms", "0 ms", "+100 ms").
    """
    number = re.compile(r'[-+−]?\d+(?:[.,]\d+)?')

    def get_number(self, value):
        match = self.number.search(value or '')
        return float(match[0].replace('−', '-').replace(',', '.')) if match else 0.0

    @staticmethod
    def get_label(number):
        milliseconds = round(number * 1000)
        sign = '+' if milliseconds > 0 else '−' if milliseconds < 0 else ''
        return f'{sign}{abs(milliseconds)} ms'


class ListGetDelayLabel(DelayValue, ScriptContainerDirectory):
    """One item labelled with the delay in milliseconds"""
    @clear_windowprops_decorator
    def get_directory(self, value='', window_prop=None, window_id=None, **kwargs):
        label = self.get_label(self.get_number(value))
        items = [self.get_list_item(label)]
        WindowProperties(window_prop, window_id).set(0, label)
        self.add_items(items)
        self.run_item_script([{'Label': label}])


class ListGetSliderRuler(DelayValue, ScriptContainerDirectory):
    """
    Items for drawing a slider value along a ruler: one item per step from minimum to maximum,
    with pad blank items on each side. Values outside the range pin the nib to the nearest end.
    Properties: fill is full, left or right where the fill from origin (default zero) to the nib crosses the item.
    The nib item has nib=true and the value in milliseconds as its label (for example "−150 ms").
    """

    @staticmethod
    def get_fill(index, zero, nib):
        lower, upper = sorted((zero, nib))
        if lower < index < upper:
            return 'full'
        if lower == upper:
            return ''
        if index == lower:
            return 'right'
        if index == upper:
            return 'left'
        return ''

    def get_directory(self, value='', minimum='-1', maximum='1', steps='80', pad='0', origin='0', **kwargs):
        minimum, maximum, steps, pad, origin = float(minimum), float(maximum), int(steps), int(pad), float(origin)
        number = self.get_number(value)

        def get_position(x):
            return max(0, min(steps, round((x - minimum) / (maximum - minimum) * steps)))

        zero, nib = get_position(origin), get_position(number)
        items = []
        for index in range(-pad, steps + pad + 1):
            path, listitem, is_folder = self.get_list_item(self.get_label(number) if index == nib else '', is_folder=False)
            if 0 <= index <= steps:
                listitem.setProperty('fill', self.get_fill(index, zero, nib))
                listitem.setProperty('nib', 'true' if index == nib else '')
            items.append((path, listitem, is_folder))
        self.add_items(items)
