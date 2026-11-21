# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import uuid
import xbmc
import xbmcgui
from jurialmunkey.ftools import cached_property
from resources.lib.sliderruler.properties import SliderRulerProperties
from resources.lib.sliderruler.scale import SliderRulerScale

PREFIX = 'SkinVariables.SliderRuler'


class SliderRulerReading:
    """Ruler value, range and owner read together in one joined label.
    The value comes first so it may contain the separator."""

    separator = '|'

    def __init__(self, label, steps):
        self.label = label
        self.steps = steps

    @cached_property
    def parts(self):
        return self.get_parts()

    def get_parts(self):
        value, minimum, maximum, origin, owner = self.label.rsplit(self.separator, 4)
        return {'value': value, 'minimum': minimum, 'maximum': maximum, 'origin': origin, 'owner': owner}

    @cached_property
    def owner(self):
        return self.parts['owner']

    @cached_property
    def scale(self):
        return self.get_scale()

    def get_scale(self):
        return SliderRulerScale(
            self.parts['value'],
            self.parts['minimum'] or '-1',
            self.parts['maximum'] or '1',
            self.steps,
            self.parts['origin'] or '0',
        )


class SliderRulerSource:
    """Skin variables that give the ruler value and range. Read with the owner property in one call on each poll,
    as each call from Python waits for Kodi to finish drawing the current frame."""

    def __init__(self, value, minimum, maximum, origin, steps):
        self.variables = (value, minimum, maximum, origin)
        self.steps = steps

    @cached_property
    def infolabel(self):
        return self.get_infolabel()

    def get_infolabel(self):
        labels = [f'$VAR[{variable}]' for variable in self.variables]
        return SliderRulerReading.separator.join((*labels, f'$INFO[Window(Home).Property({PREFIX}.Owner)]'))

    def read(self):
        return SliderRulerReading(xbmc.getInfoLabel(self.infolabel), self.steps)


class SliderRulerMonitor:
    """
    Sets the ruler properties on the home window while the slider window is open.
    Static ruler items compare their step index with SkinVariables.SliderRuler.Lower, .Upper and .Nib, and show .Label.
    Ready is set with the first values. Only changed values are written on each poll, through builtins that Kodi
    applies together on its next frame without making the script wait.
    Owner names the running monitor. The skin clears it when the window closes, and a monitor started for a window
    opened again replaces it, so the monitor stops once Owner is no longer its own.
    Visibility is also checked every few polls in case the window closes without clearing Owner.
    """

    visibility_polls = 20

    def __init__(self, window, source, polling):
        self.window = window
        self.source = source
        self.polling = polling
        self.values = {}
        self.polls = 0

    @cached_property
    def home(self):
        return xbmcgui.Window(10000)

    @cached_property
    def monitor(self):
        return xbmc.Monitor()

    @cached_property
    def owner(self):
        return uuid.uuid4().hex

    @classmethod
    def set_property(cls, key, value):
        if not value:
            return cls.clear_property(key)
        xbmc.executebuiltin(f'SetProperty({PREFIX}.{key},{value},home)')

    @classmethod
    def clear_property(cls, key):
        xbmc.executebuiltin(f'ClearProperty({PREFIX}.{key},home)')

    @property
    def is_visible(self):
        return xbmc.getCondVisibility(f'Window.IsVisible({self.window})')

    @property
    def is_checking_visibility(self):
        return self.polls % self.visibility_polls == 0

    def is_active(self, reading):
        if reading.owner != self.owner:
            return False
        return not self.is_checking_visibility or self.is_visible

    def update(self, reading):
        properties = SliderRulerProperties(reading.scale)
        for key, value in properties.get_changes(self.values).items():
            self.set_property(key, value)
        self.values = properties.values

    def wait(self):
        """The next reading while the window stays open, otherwise None"""
        self.polls += 1
        if self.monitor.waitForAbort(self.polling):
            return
        reading = self.source.read()
        return reading if self.is_active(reading) else None

    def clear(self):
        owner = self.home.getProperty(f'{PREFIX}.Owner')
        if owner not in (self.owner, ''):
            return
        for key in (*(key for key, value in self.values.items() if value), 'Ready', 'Owner'):
            self.clear_property(key)

    def run(self):
        # Set directly rather than through a builtin so the first reading already sees it.
        self.home.setProperty(f'{PREFIX}.Owner', self.owner)
        try:
            self.update(self.source.read())
            self.set_property('Ready', 'true')
            for reading in iter(self.wait, None):
                self.update(reading)
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
