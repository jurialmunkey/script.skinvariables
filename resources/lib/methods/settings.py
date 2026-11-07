# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from jurialmunkey.jsnrpc import get_jsonrpc
from jurialmunkey.parser import boolean


class KodiSettingUpdate:
    def __init__(self, setting, value):
        self.setting = setting
        self.value = value

    @cached_property
    def current(self):
        return self.get_current()

    def get_current(self):
        return get_jsonrpc('Settings.GetSettingValue', {'setting': self.setting}).get('result', {}).get('value')

    @cached_property
    def converted_value(self):
        return self.get_converted_value()

    def get_converted_value(self):
        # bool must precede int because bool is an int subclass.
        if isinstance(self.current, bool):
            return not self.current if self.value == 'toggle' else boolean(self.value)
        if isinstance(self.current, int):
            return int(self.value)
        if isinstance(self.current, float):
            return float(self.value)
        return self.value

    def run(self):
        if self.value is None or self.current is None:
            return
        try:
            value = self.converted_value
        except ValueError:
            return
        get_jsonrpc('Settings.SetSettingValue', {'setting': self.setting, 'value': value})


def set_kodisetting(set_kodisetting, value=None, **kwargs):
    KodiSettingUpdate(set_kodisetting, value).run()
