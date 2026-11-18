# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from jurialmunkey.ftools import cached_property


class SettingValue:
    """Current value of a Kodi setting as JSON-RPC gives it, with the text shown for it."""

    def __init__(self, meta):
        self.meta = meta

    @property
    def is_enabled(self):
        return self.meta['enabled']

    @property
    def value(self):
        return self.meta['value']

    @property
    def control(self):
        return self.meta['control']

    @cached_property
    def text(self):
        return self.get_text()

    def get_text(self):
        return str(self.value)


class MissingValue(SettingValue):
    """Setting that Kodi no longer shows, such as one hidden by a change to the setting it depends on.

    Its controls are hidden so sliders are left at their first position.
    """

    value = None
    position = 0
    maximum_position = 0

    def __init__(self):
        super().__init__({})

    @property
    def is_enabled(self):
        return False

    def get_text(self):
        return ''


class ChoicesValue(SettingValue):
    """Setting whose value is one of a list of choices. The choices are labels with their values."""

    @cached_property
    def choices(self):
        return self.get_choices()

    def get_choices(self):
        raise NotImplementedError

    @cached_property
    def labels(self):
        return {str(value): label for label, value in self.choices}

    def get_position(self, value):
        """Position of the value in the choices or -1 when it is not one of them."""
        return next((position for position, (label, choice) in enumerate(self.choices) if choice == value), -1)

    @property
    def position(self):
        return self.get_position(self.value)

    def get_text(self):
        # Values missing from the choices are shown as they are, as Kodi does for values it cannot find.
        return self.labels.get(str(self.value), str(self.value))


class ActionValue(SettingValue):
    """Setting that runs an action when clicked. It has no value to show."""

    def get_text(self):
        return ''


class BooleanValue(SettingValue):
    on_label_id = 16041
    off_label_id = 16039

    def get_text(self):
        return xbmc.getLocalizedString(self.on_label_id if self.value else self.off_label_id)


class HiddenValue(SettingValue):
    """Setting whose edit control hides its text, such as a password. Shows a mask without the length of the text."""

    mask = '*****'

    def get_text(self):
        return self.mask if self.value else ''


class OptionsValue(ChoicesValue):
    """Setting with a list of options. Shows the label of the selected option."""

    def get_choices(self):
        return [(option['label'], option['value']) for option in self.meta['options']]


class RangeValue(ChoicesValue):
    """Number setting that steps from its minimum to its maximum. Each step is labelled as Kodi's controls show it.

    Kodi's format labels use Python format fields such as "{0:d} ms". Spinners can label the minimum, such as "Off".
    """

    @cached_property
    def steps(self):
        return self.get_steps()

    def get_steps(self):
        minimum, step = self.meta['minimum'], self.meta['step']
        count = round((self.meta['maximum'] - minimum) / step)
        # Rounding keeps decimal steps such as 0.1 from gathering floating point errors.
        return [type(minimum)(round(minimum + position * step, 6)) for position in range(count + 1)]

    @property
    def maximum_position(self):
        return len(self.steps) - 1

    def get_step_label(self, value):
        if value == self.meta['minimum'] and self.control.get('minimumlabel'):
            return self.control['minimumlabel']
        if self.control.get('formatlabel'):
            return self.control['formatlabel'].format(value)
        return f'{value} %' if self.control['format'] == 'percentage' else str(value)

    def get_choices(self):
        return [(self.get_step_label(value), value) for value in self.steps]

    def get_text(self):
        return self.get_step_label(self.value)


class AddonValue(SettingValue):
    """Setting that selects an add-on. Shows the name of the installed add-on."""

    def get_text(self):
        return xbmc.getInfoLabel(f'System.AddonTitle({self.value})') if self.value else ''


class ListValue(SettingValue):
    """Setting that holds several values. Each value is shown as its element definition shows it."""

    separator = ', '

    def get_element(self, value):
        return get_setting_value({**self.meta['definition'], 'value': value})

    @cached_property
    def element_choices(self):
        """Choices of each element. Elements of Kodi's list settings choose from options or a range."""
        return self.get_element(None).choices

    @property
    def positions(self):
        return [position for position, (label, value) in enumerate(self.element_choices) if value in self.value]

    def get_text(self):
        return self.separator.join(self.get_element(value).text for value in self.value)


VALUE_CLASSES = {
    'action': ActionValue,
    'boolean': BooleanValue,
    'addon': AddonValue,
    'list': ListValue,
}


def get_setting_value(meta):
    # Kodi only gives the hidden flag for edit controls.
    if meta['control'].get('hidden'):
        return HiddenValue(meta)
    if 'options' in meta:
        return OptionsValue(meta)
    # Kodi gives a minimum for number settings that step through a range instead of listing options.
    if 'minimum' in meta:
        return RangeValue(meta)
    return VALUE_CLASSES.get(meta['type'], SettingValue)(meta)
