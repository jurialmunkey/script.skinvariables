# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmcvfs
from resources.lib.skinsettings.template import SkinSettingsTemplate


class SettingSearchTemplate(SkinSettingsTemplate):
    """Builds the settings search from a skin template file written for it, separate from the skin settings one.

    The settings search has no categories so the category list is removed when the template has one.
    """

    filename = 'script-skinvariables-settingsearch.xml'
    template_ids = {**SkinSettingsTemplate.template_ids, 'level': '20'}
    default_ids = SkinSettingsTemplate.default_ids + (SkinSettingsTemplate.category_list_id,)

    def get_placed_items(self):
        # The tags and level buttons are optional so only the buttons the skin placed are configured.
        return [item for item in super().get_placed_items() if self.template_ids[item.template] in self.controls]

    def get_document(self):
        settings_elements = self.settings_elements
        self.remove_default_elements()
        self.configure_placed_items()
        self.controls[self.settings_list_id].element.extend(settings_elements)
        return self.root


class SettingSearchCategoryTemplate(SettingSearchTemplate):
    """Builds the settings search from the skin's SettingsCategory.xml when the skin has no template for it."""

    filename = 'SettingsCategory.xml'


def get_settingsearch_template(folder, definition):
    exists = xbmcvfs.exists(SettingSearchTemplate.get_filepath(folder))
    template_class = SettingSearchTemplate if exists else SettingSearchCategoryTemplate
    return template_class(folder, definition)
