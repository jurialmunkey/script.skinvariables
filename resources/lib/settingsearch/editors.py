# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from urllib.parse import quote, unquote
import xbmc
import xbmcgui
from jurialmunkey.ftools import cached_property
from resources.lib.settingsearch.closeactions import SettingNavigation, get_setting_change
from resources.lib.settingsearch.kodisettings import KodiAddons, KodiSettingLevel


class SettingEditor:
    """Asks for a new value of a Kodi setting with the dialog Kodi's settings windows use for its control.

    Editors return None when the dialog is cancelled. Kodi settings never hold None so it cannot be a new value.
    """

    def __init__(self, item):
        self.item = item

    @property
    def current(self):
        return self.item.current

    @property
    def value(self):
        return self.current.value

    @property
    def control(self):
        return self.current.control

    @property
    def heading(self):
        # Kodi gives a heading for some controls and uses the setting label for the others.
        return self.control.get('heading') or self.item.label_text

    def get_value(self):
        raise NotImplementedError

    def edit(self, window):
        value = self.get_value()
        if value is None or value == self.value:
            return
        get_setting_change(self.item.setting, value).apply(window)


class OpenWindowEditor(SettingEditor):
    """Opens the setting in its settings window for controls a script cannot change, such as actions.

    Kodi only shows settings up to the level of its settings windows. Settings above that level open their category.
    """

    def get_focus_target(self, level):
        setting = self.item.setting
        return setting.key if setting.level <= level else setting.category.key

    def edit(self, window):
        # Kodi's level is read on each click because it can change in its settings windows.
        target = self.get_focus_target(KodiSettingLevel().rank)
        window.close_with(SettingNavigation(self.item.setting.window, target))


class ToggleEditor(SettingEditor):
    def get_value(self):
        return not self.value


class SelectEditor(SettingEditor):
    """Lists the choices of the setting with the current choice selected."""

    @property
    def choices(self):
        return self.current.choices

    @property
    def preselect(self):
        return self.current.position

    def get_value(self):
        labels = [label for label, value in self.choices]
        position = xbmcgui.Dialog().select(self.heading, labels, preselect=self.preselect)
        return self.choices[position][1] if position != -1 else None


class AddonEditor(SelectEditor):
    """Lists the enabled add-ons of the type the setting selects. Settings that can be empty also list None."""

    none_label_id = 231

    @cached_property
    def choices(self):
        return self.get_choices()

    def get_choices(self):
        none = [(xbmc.getLocalizedString(self.none_label_id), '')] if self.current.meta['allowempty'] else []
        return none + KodiAddons(self.current.meta['addontype']).choices

    @property
    def preselect(self):
        return next((position for position, (label, value) in enumerate(self.choices) if value == self.value), -1)


class MultiSelectEditor(SettingEditor):
    """Lists the choices of each element of a list setting with the current elements selected."""

    def get_value(self):
        choices = self.current.element_choices
        labels = [label for label, value in choices]
        positions = xbmcgui.Dialog().multiselect(self.heading, labels, preselect=self.current.positions)
        return [choices[position][1] for position in positions] if positions is not None else None


class KeyboardEditor(SettingEditor):
    """Edits the text of the setting with Kodi's keyboard. Hidden settings hide the text as it is typed."""

    def get_default(self):
        return str(self.value)

    def get_setting_value(self, text):
        return text

    def get_value(self):
        keyboard = xbmc.Keyboard(self.get_default(), self.heading, bool(self.control.get('hidden')))
        keyboard.doModal()
        return self.get_setting_value(keyboard.getText()) if keyboard.isConfirmed() else None


class URLEncodedEditor(KeyboardEditor):
    """Edits the decoded text of a setting that Kodi stores URL encoded."""

    def get_default(self):
        return unquote(self.value)

    def get_setting_value(self, text):
        return quote(text)


class NumberEditor(KeyboardEditor):
    """Edits a decimal number. Text that is not a number leaves the setting unchanged."""

    def get_setting_value(self, text):
        try:
            return float(text)
        except ValueError:
            return None


class NumericEditor(SettingEditor):
    """Edits the setting with Kodi's numeric dialog, which returns empty text when cancelled."""

    numeric_type = 0

    def get_default(self):
        return str(self.value)

    def get_setting_value(self, text):
        return text

    def get_value(self):
        text = xbmcgui.Dialog().numeric(self.numeric_type, self.heading, self.get_default())
        return self.get_setting_value(text) if text else None


class IntegerEditor(NumericEditor):
    def get_setting_value(self, text):
        return int(text)


class IPAddressEditor(NumericEditor):
    numeric_type = 3


class DateEditor(NumericEditor):
    """Edits a date. Kodi stores dates as YYYY-MM-DD and its dialog uses DD/MM/YYYY."""

    numeric_type = 1

    def get_default(self):
        return '/'.join(reversed(self.value.split('-')))

    def get_setting_value(self, text):
        return '-'.join(reversed([part.strip().zfill(2) for part in text.split('/')]))


class TimeEditor(NumericEditor):
    numeric_type = 2

    def get_setting_value(self, text):
        return ':'.join(part.strip().zfill(2) for part in text.split(':'))


class PasswordEditor(SettingEditor):
    """Asks for a password that Kodi stores as its MD5 hash. Kodi's dialog returns the hash."""

    def get_value(self):
        option = xbmcgui.PASSWORD_VERIFY if self.control.get('verifynewvalue') else 0
        return xbmcgui.Dialog().input(self.heading, type=xbmcgui.INPUT_PASSWORD, option=option) or None


class BrowseEditor(SettingEditor):
    """Browses for a folder, file or image. Kodi's dialog returns the current value when cancelled."""

    browse_type = 0

    @property
    def shares(self):
        # Settings limited to local sources browse local drives. The others can also browse network sources.
        return 'local' if self.current.meta['sources'] == ['local'] else 'files'

    def get_browse_type(self):
        return self.browse_type

    def get_value(self):
        return xbmcgui.Dialog().browse(self.get_browse_type(), self.heading, self.shares, defaultt=self.value)


class FolderEditor(BrowseEditor):
    writable_browse_type = 3

    def get_browse_type(self):
        return self.writable_browse_type if self.current.meta['writable'] else self.browse_type


class FileEditor(BrowseEditor):
    browse_type = 1


class ImageEditor(BrowseEditor):
    browse_type = 2


class ColourEditor(SettingEditor):
    """Picks a colour with Kodi's colour picker, which returns empty text when cancelled."""

    def get_value(self):
        return xbmcgui.Dialog().colorpicker(self.heading, selectedcolor=self.value) or None


# Editors by Kodi control type and format. Controls not listed open the setting in its settings window.
FORMAT_EDITORS = {
    ('edit', 'string'): KeyboardEditor,
    ('edit', 'urlencoded'): URLEncodedEditor,
    ('edit', 'integer'): IntegerEditor,
    ('edit', 'number'): NumberEditor,
    ('edit', 'ip'): IPAddressEditor,
    ('edit', 'md5'): PasswordEditor,
    ('button', 'addon'): AddonEditor,
    ('button', 'path'): FolderEditor,
    ('button', 'file'): FileEditor,
    ('button', 'image'): ImageEditor,
    ('button', 'date'): DateEditor,
    ('button', 'time'): TimeEditor,
}
CONTROL_EDITORS = {
    'toggle': ToggleEditor,
    'list': SelectEditor,
    'spinner': SelectEditor,
    'colorbutton': ColourEditor,
}


def get_setting_editor(item):
    meta = item.setting.meta
    # List settings hold several values so Kodi lets several choices be selected.
    if meta['type'] == 'list':
        return MultiSelectEditor(item)
    control = meta['control']
    editor_class = FORMAT_EDITORS.get((control['type'], control['format']))
    return (editor_class or CONTROL_EDITORS.get(control['type'], OpenWindowEditor))(item)
