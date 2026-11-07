# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from jurialmunkey.litems import ContainerDirectory
from resources.lib.lists.koditools.common import WindowProperties, clear_windowprops_decorator
from resources.lib.methods.controls import set_slider


class ARGBChannel:
    def __init__(self, colorhex, name, start):
        self.colorhex = colorhex
        self.name = name
        self.start = start

    @cached_property
    def hex(self):
        return self.get_hex()

    def get_hex(self):
        return self.colorhex[self.start:self.start + 2]

    @cached_property
    def value(self):
        return self.get_value()

    def get_value(self):
        return int(self.hex, 16)

    @cached_property
    def percent(self):
        return self.get_percent()

    def get_percent(self):
        return int(self.value / 255 * 100)

    @cached_property
    def properties(self):
        return self.get_properties()

    def get_properties(self):
        return {f'{self.name}.hex': self.hex, f'{self.name}.int': self.value, f'{self.name}.pct': self.percent}


class ARGBSliders:
    def __init__(self, window_id, controls):
        self.window_id = window_id
        self.controls = controls

    def update(self, channel):
        control_id = self.controls.get(f'slider_{channel.name}_id')
        if not self.window_id or not control_id:
            return
        try:
            set_slider(self.window_id, control_id, channel.percent)
        except (RuntimeError, ValueError, TypeError, AttributeError):
            pass


class ARGBColor:
    def __init__(self, colorhex, sliders):
        self.colorhex = colorhex
        self.sliders = sliders

    @cached_property
    def channels(self):
        return self.get_channels()

    def get_channels(self):
        return [
            ARGBChannel(self.colorhex, name, index * 2)
            for index, name in enumerate(('alpha', 'red', 'green', 'blue'))
        ]

    @cached_property
    def properties(self):
        return self.get_properties()

    def get_properties(self):
        properties = {}
        for channel in self.channels:
            properties.update(channel.properties)
            self.sliders.update(channel)
        return properties


class ListGetARGBColors(ContainerDirectory):
    @clear_windowprops_decorator
    def get_directory(self, colorhex=None, window_prop=None, window_id=None, slider_window_id=None, **kwargs):
        if not colorhex:
            return
        color = ARGBColor(colorhex, ARGBSliders(slider_window_id, kwargs))
        infoproperties = color.properties
        item = self.get_list_item(colorhex)
        item[1].setProperties(infoproperties)
        WindowProperties(window_prop, window_id).write(infoproperties)
        self.add_items([item])
