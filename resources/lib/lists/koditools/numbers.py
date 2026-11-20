# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.window import get_property
from resources.lib.lists.koditools.common import WindowProperties, clear_windowprops_decorator
from resources.lib.lists.koditools.scripts import ScriptContainerDirectory
from resources.lib.sliderruler.scale import DelayValue, SliderRulerScale


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


class ListGetDelayLabel(DelayValue, ScriptContainerDirectory):
    """One item labelled with the delay in milliseconds"""
    @clear_windowprops_decorator
    def get_directory(self, value='', window_prop=None, window_id=None, **kwargs):
        label = self.get_label(self.get_number(value))
        items = [self.get_list_item(label)]
        WindowProperties(window_prop, window_id).set(0, label)
        self.add_items(items)
        self.run_item_script([{'Label': label}])


class ListGetSliderRuler(ScriptContainerDirectory):
    """
    Items for drawing a slider value along a ruler: one item per step from minimum to maximum,
    with pad blank items on each side. Values outside the range pin the nib to the nearest end.
    Properties: fill is full, left or right where the fill from origin (default zero) to the nib crosses the item.
    The nib item has nib=true and the value in milliseconds as its label (for example "−150 ms").
    Skins can draw the same ruler from static items with RunScript(script.skinvariables,run_sliderruler) instead,
    which follows the value without reloading the list.
    """

    def get_item(self, scale, index):
        path, listitem, is_folder = self.get_list_item(scale.label if index == scale.nib else '', is_folder=False)
        if index in scale.indices:
            listitem.setProperty('fill', scale.get_fill(index))
            listitem.setProperty('nib', scale.get_nib(index))
        return (path, listitem, is_folder)

    def get_directory(self, value='', minimum='-1', maximum='1', steps='80', pad='0', origin='0', **kwargs):
        scale = SliderRulerScale(value, minimum, maximum, steps, origin)
        pad = int(pad)
        self.add_items([self.get_item(scale, index) for index in range(-pad, scale.steps + pad + 1)])
