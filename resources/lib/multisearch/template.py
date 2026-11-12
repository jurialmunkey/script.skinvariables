# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.scriptwindow.controller import ScriptWindowFile
from resources.lib.scriptwindow.template import ScriptWindowTemplate


class MultiSearchWindowTemplate(ScriptWindowTemplate):
    """Builds the multi search window from the skin's window file.

    The source grouplist is optional. When the skin has both the grouplist and its button template, the grouplist is
    filled with a button for all sources followed by a button for each source.
    """

    filename = 'script-skinvariables-multisearch.xml'
    grouplist_id = '200'
    template_ids = {
        'button': '201',
    }
    default_ids = ('201',)

    def __init__(self, folder, buttons):
        super().__init__(folder)
        self.buttons = buttons

    @cached_property
    def has_grouplist(self):
        return self.get_has_grouplist()

    def get_has_grouplist(self):
        return {self.grouplist_id, self.template_ids['button']}.issubset(self.controls)

    @cached_property
    def elements(self):
        return self.get_elements()

    def get_elements(self):
        return [self.get_element(item) for item in self.buttons.items]

    def add_buttons(self):
        if not self.has_grouplist:
            return
        elements = self.elements
        self.remove_default_elements()
        self.controls[self.grouplist_id].element.extend(elements)

    def get_document(self):
        self.add_buttons()
        return self.root


class MultiSearchWindowFile(ScriptWindowFile):
    basefolder = 'special://profile/addon_data/script.skinvariables/multisearch/'
    filename = 'script-skinvariables-multisearch-generated.xml'

    def __init__(self, folder, buttons):
        super().__init__(folder)
        self.buttons = buttons

    def get_template(self):
        return MultiSearchWindowTemplate(self.folder, self.buttons)
