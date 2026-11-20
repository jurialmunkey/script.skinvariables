# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import uuid
import xbmc
import xbmcgui
from jurialmunkey.ftools import cached_property
from resources.lib.sliderruler.properties import SliderRulerProperties
from resources.lib.sliderruler.scale import SliderRulerScale


class SliderRulerSource:
    """Skin variables that give the ruler value and range. Read again on each poll so they follow the dialog."""

    def __init__(self, value, minimum, maximum, origin, steps):
        self.variables = (value, minimum, maximum, origin)
        self.steps = steps

    @staticmethod
    def get_label(variable):
        return xbmc.getInfoLabel(f'$VAR[{variable}]')

    @property
    def scale(self):
        return self.get_scale()

    def get_scale(self):
        value, minimum, maximum, origin = (self.get_label(variable) for variable in self.variables)
        return SliderRulerScale(value, minimum or '-1', maximum or '1', self.steps, origin or '0')


class SliderRulerMonitor:
    """
    Sets the ruler properties on the home window while the slider window is visible.
    Static ruler items read SkinVariables.SliderRuler.{index}.Fill, .{index}.Nib and .Label from these properties.
    Ready is set once the first values are written. Only changed values are written on each poll.
    Owner names the running monitor so a monitor for a window opened again stops the previous one.
    """

    prefix = 'SkinVariables.SliderRuler'

    def __init__(self, window, source, polling):
        self.window = window
        self.source = source
        self.polling = polling
        self.values = {}

    @cached_property
    def home(self):
        return xbmcgui.Window(10000)

    @cached_property
    def monitor(self):
        return xbmc.Monitor()

    @cached_property
    def owner(self):
        return uuid.uuid4().hex

    def get_property(self, key):
        return self.home.getProperty(f'{self.prefix}.{key}')

    def set_property(self, key, value):
        self.home.setProperty(f'{self.prefix}.{key}', value)

    def clear_property(self, key):
        self.home.clearProperty(f'{self.prefix}.{key}')

    @property
    def is_owner(self):
        return self.get_property('Owner') == self.owner

    @property
    def is_visible(self):
        return xbmc.getCondVisibility(f'Window.IsVisible({self.window})')

    @property
    def is_active(self):
        return self.is_owner and self.is_visible

    def wait(self):
        """True while the window stays open after waiting for the next poll"""
        return not self.monitor.waitForAbort(self.polling) and self.is_active

    def update(self):
        properties = SliderRulerProperties(self.source.scale)
        for key, value in properties.get_changes(self.values).items():
            self.set_property(key, value)
        self.values = properties.values

    def clear(self):
        if not self.is_owner:
            return
        for key in (*self.values, 'Ready', 'Owner'):
            self.clear_property(key)

    def run(self):
        self.set_property('Owner', self.owner)
        try:
            self.update()
            self.set_property('Ready', 'true')
            while self.wait():
                self.update()
        finally:
            self.clear()


def run_sliderruler(
    run_sliderruler,
    window='DialogSlider.xml',
    value='',
    minimum='',
    maximum='',
    origin='',
    steps='80',
    polling='0.03',
    **kwargs,
):
    source = SliderRulerSource(value, minimum, maximum, origin, steps)
    SliderRulerMonitor(window, source, float(polling)).run()
