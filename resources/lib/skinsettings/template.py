# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmcvfs
from jurialmunkey.ftools import cached_property
from resources.lib.scriptwindow.template import ScriptWindowTemplate


class SkinSettingsTemplate(ScriptWindowTemplate):
    """Builds the scripted window from a skin template file written for the script."""

    filename = 'script-skinvariables-skinsettings.xml'
    category_list_id = '3'
    settings_list_id = '5'
    template_ids = {
        'category': '10',
        'group': '14',
        'button': '7',
        'radiobutton': '8',
        'edit': '12',
    }
    # Kodi hides its default template controls in native settings windows so the script removes them.
    default_ids = ('7', '8', '9', '10', '11', '12', '13', '14', '15')

    def __init__(self, folder, definition):
        super().__init__(folder)
        self.definition = definition

    @cached_property
    def category_elements(self):
        return self.get_category_elements()

    def get_category_elements(self):
        return [self.get_element(category) for category in self.definition.categories]

    @cached_property
    def settings_elements(self):
        return self.get_settings_elements()

    def get_settings_elements(self):
        return [self.get_element(item) for item in self.definition.layout]

    def get_placed_ids(self):
        return {self.template_ids[item.template] for item in self.definition.search.placed_items}

    def configure_placed_items(self):
        for item in self.definition.search.placed_items:
            self.get_template(item.template).configure(item)

    def get_document(self):
        category_elements, settings_elements = self.category_elements, self.settings_elements
        self.remove_default_elements()
        self.configure_placed_items()
        self.controls[self.category_list_id].element.extend(category_elements)
        self.controls[self.settings_list_id].element.extend(settings_elements)
        return self.root


class SettingsCategoryTemplate(SkinSettingsTemplate):
    """Builds the scripted window from the skin's SettingsCategory.xml when the skin has no script template."""

    filename = 'SettingsCategory.xml'


def get_skinsettings_template(folder, definition):
    exists = xbmcvfs.exists(SkinSettingsTemplate.get_filepath(folder))
    template_class = SkinSettingsTemplate if exists else SettingsCategoryTemplate
    return template_class(folder, definition)
