# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmcgui
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import load_filecontent
from jurialmunkey.parser import boolean
from resources.lib.methods.builtins import executebuiltin
from resources.lib.methods.preselection import DialogSelectPreselectedItems, DialogMultiSelectPreselectedItems


HEADING = ('heading', str, '')
MESSAGE = ('message', 'get_content', '')
YESNO_PARAMETERS = (HEADING, MESSAGE, ('nolabel', str, 'No'), ('yeslabel', str, 'Yes'))
YESNO_BUTTONS = (('defaultbutton', int, xbmcgui.DLG_YESNO_YES_BTN), ('autoclose', int, 0))


class DialogRunner:
    method = None
    parameters = ()
    values_key = None

    def __init__(self, params, separator=' / '):
        self.params = params
        self.separator = separator

    def get_items(self, value):
        return value.split(self.separator)

    def get_content(self, value):
        return str(load_filecontent(value)) if boolean(self.params.get('load_file')) else str(value)

    def get_argument(self, key, converter, fallback):
        converter = getattr(self, converter) if isinstance(converter, str) else converter
        return converter(self.params.get(key) or fallback)

    @cached_property
    def arguments(self):
        return self.get_arguments()

    def get_arguments(self):
        return {key: self.get_argument(key, converter, fallback) for key, converter, fallback in self.parameters}

    @cached_property
    def values(self):
        return self.get_values()

    def get_values(self):
        return self.arguments.get(self.values_key)

    def run(self):
        output = getattr(xbmcgui.Dialog(), self.method)(**self.arguments)
        if not isinstance(output, (tuple, list)):
            output = (output,)
        for index in output:
            executebuiltin(index=index, values=self.values, **self.params)


class OkDialog(DialogRunner):
    method = 'ok'
    parameters = (HEADING, MESSAGE)


class YesNoDialog(DialogRunner):
    method = 'yesno'
    parameters = YESNO_PARAMETERS + YESNO_BUTTONS


class YesNoCustomDialog(DialogRunner):
    method = 'yesnocustom'
    parameters = YESNO_PARAMETERS + (('customlabel', str, 'Custom'),) + YESNO_BUTTONS


class TextViewerDialog(DialogRunner):
    method = 'textviewer'
    parameters = (HEADING, ('text', 'get_content', ''), ('usemono', boolean, True))


class NotificationDialog(DialogRunner):
    method = 'notification'
    parameters = (HEADING, ('message', str, ''), ('icon', str, ''), ('time', int, 5000), ('sound', boolean, True))


class NumericDialog(DialogRunner):
    method = 'numeric'
    parameters = (HEADING, ('defaultt', str, ''), ('type', int, 0), ('bHiddenInput', boolean, False))


class InputDialog(DialogRunner):
    method = 'input'
    parameters = (
        HEADING,
        ('defaultt', str, ''),
        ('type', int, xbmcgui.INPUT_ALPHANUM),
        ('option', int, 0),
        ('autoclose', int, 0),
    )


class BrowseDialog(DialogRunner):
    method = 'browse'
    parameters = (
        HEADING,
        ('shares', str, ''),
        ('mask', str, ''),
        ('defaultt', str, ''),
        ('type', int, 0),
        ('useThumbs', boolean, True),
        ('treatAsFolder', boolean, True),
        ('enableMultiple', boolean, True),
    )


class ColorPickerDialog(DialogRunner):
    method = 'colorpicker'
    parameters = (HEADING, ('selectedcolor', str, ''), ('colorfile', str, ''))


class ContextMenuDialog(DialogRunner):
    method = 'contextmenu'
    parameters = (('list', 'get_items', ''),)


class SelectDialog(DialogRunner):
    method = 'select'
    values_key = 'list'
    preselection_class = DialogSelectPreselectedItems
    parameters = (
        HEADING,
        ('list', 'get_items', ''),
        ('autoclose', int, 0),
        ('preselect', 'get_preselect', None),
        ('useDetails', boolean, False),
    )

    def get_preselect(self, value):
        items = self.get_items(self.params.get(self.values_key) or '')
        values = self.get_items(value or '')
        return self.preselection_class(values, items).preselected_items


class MultiSelectDialog(SelectDialog):
    method = 'multiselect'
    values_key = 'options'
    preselection_class = DialogMultiSelectPreselectedItems
    parameters = (
        HEADING,
        ('options', 'get_items', ''),
        ('autoclose', int, 0),
        ('preselect', 'get_preselect', None),
        ('useDetails', boolean, False),
    )


DIALOG_CLASSES = {
    'ok': OkDialog,
    'yesno': YesNoDialog,
    'yesnocustom': YesNoCustomDialog,
    'textviewer': TextViewerDialog,
    'notification': NotificationDialog,
    'numeric': NumericDialog,
    'input': InputDialog,
    'browse': BrowseDialog,
    'colorpicker': ColorPickerDialog,
    'contextmenu': ContextMenuDialog,
    'select': SelectDialog,
    'multiselect': MultiSelectDialog,
}


def run_dialog(run_dialog, separator=' / ', **kwargs):
    DIALOG_CLASSES[run_dialog](kwargs, separator).run()
