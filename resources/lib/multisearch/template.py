# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.multisearch.sourcelist import SOURCE_LIST_ID
from resources.lib.scriptwindow.controller import ScriptWindowFile
from resources.lib.scriptwindow.template import ScriptWindowTemplate


class MultiSearchWindowTemplate(ScriptWindowTemplate):
    """Builds the multi search window from the skin's window file.

    The source list is optional. The window fills it with the shown source buttons when the skin has it.

    When the skin defines results containers by widget style, each one in the window file is only visible while the
    results use it.
    """

    filename = 'script-skinvariables-multisearch.xml'

    def __init__(self, folder, containers):
        super().__init__(folder)
        self.containers = containers

    @cached_property
    def has_source_list(self):
        return str(SOURCE_LIST_ID) in self.controls

    @cached_property
    def container_controls(self):
        """Results containers in the window file that are shown only while the results use them."""
        return self.get_container_controls()

    def get_container_controls(self):
        return {
            control_id: self.controls[str(control_id)]
            for control_id in self.containers.toggled_ids
            if str(control_id) in self.controls
        }

    def add_container_conditions(self):
        for control_id, control in self.container_controls.items():
            condition = self.containers.get_visible_condition(control_id)
            control.element.append(control.get_override_element('visible', condition, {}))

    def get_document(self):
        self.add_container_conditions()
        return self.root


class MultiSearchWindowFile(ScriptWindowFile):
    basefolder = 'special://profile/addon_data/script.skinvariables/multisearch/'
    filename = 'script-skinvariables-multisearch-generated.xml'

    def __init__(self, folder, containers):
        super().__init__(folder)
        self.containers = containers

    def get_template(self):
        return MultiSearchWindowTemplate(self.folder, self.containers)
