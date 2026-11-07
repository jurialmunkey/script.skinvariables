# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc


class SkinStringHistory:
    def __init__(self, name, value, separator='|', toggle=False):
        self.name = name
        self.value = value
        self.separator = separator
        self.toggle = toggle

    @property
    def infolabel(self):
        return self.get_infolabel()

    def get_infolabel(self):
        return f'Skin.String({self.name})'

    @property
    def updated_value(self):
        return self.get_updated_value()

    def get_updated_value(self):
        values = (xbmc.getInfoLabel(self.infolabel) or '').split(self.separator)
        try:
            values.remove(self.value)
            removed = True
        except ValueError:
            removed = False
        if not self.toggle or not removed:
            values.insert(0, self.value)
        return self.separator.join(filter(None, values))

    @property
    def command(self):
        return self.get_command()

    def get_command(self):
        return f'Skin.SetString({self.name},{self.updated_value})'

    def run(self):
        xbmc.executebuiltin(self.command)


class WindowPropertyHistory(SkinStringHistory):
    def __init__(self, name, value, separator='|', toggle=False, window_id=''):
        super().__init__(name, value, separator, toggle)
        self.window_id = window_id

    def get_infolabel(self):
        window = f'Window({self.window_id})' if self.window_id else 'Window'
        return f'{window}.Property({self.name})'

    def get_command(self):
        affix = f',{self.window_id}' if self.window_id else ''
        return f'SetProperty({self.name},{self.updated_value}{affix})'


def add_skinstring_history(
    add_skinstring_history,
    value,
    separator='|',
    use_window_prop=False,
    window_id='',
    toggle=False,
    **kwargs,
):
    if use_window_prop:
        history = WindowPropertyHistory(add_skinstring_history, value, separator, toggle, window_id)
    else:
        history = SkinStringHistory(add_skinstring_history, value, separator, toggle)
    history.run()
