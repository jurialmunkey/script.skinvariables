# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from jurialmunkey.ftools import cached_property
from resources.lib.settingsearch.editors import get_setting_editor
from resources.lib.settingsearch.kodisettings import KodiSettingChange
from resources.lib.settingsearch.values import MissingValue, get_setting_value
from resources.lib.skinsettings.items import (
    ButtonSetting,
    RadioButtonSetting,
    SettingsLabel,
    SettingsListItem,
    PROPERTY_PREFIX,
    get_label_info,
    get_label_text,
)
from resources.lib.skinsettings.slider import SliderSetting


HEADING_ID_START = -400000
KODI_SETTING_ID_START = -500000
SKIN_LABEL_ID = 166


class SettingHeading(SettingsLabel):
    """Label written as "Window > Category" above the matching settings of a category.

    Its tags are the window and category labels so its settings can be filtered by either.
    """

    control_id_start = HEADING_ID_START
    template = 'group'

    def __init__(self, key, meta, rank, search):
        super().__init__(key, meta, rank, None, search)

    def get_order(self):
        return (self.rank,)

    def get_visible_conditions(self):
        # Headings show while one of their settings matches the search and is visible.
        return [self.shown_condition, self.settings_condition]


class KodiHeading(SettingHeading):
    """Heading of a category in Kodi's settings windows."""

    def __init__(self, category, rank, search):
        meta = {'label': f'{category.section.label} > {category.label}'}
        super().__init__(f'{category.section.key}.{category.key}', meta, rank, search)
        self.kodi_category = category

    def get_tags(self):
        return [self.kodi_category.section.label, self.kodi_category.label]


class SkinHeading(SettingHeading):
    """Heading of a category in the skin settings. Groups of the skin settings place their settings under it."""

    @property
    def category_label(self):
        return str(self.meta.get('label', ''))

    @property
    def label(self):
        return f'$LOCALIZE[{SKIN_LABEL_ID}] > {get_label_info(self.category_label)}'

    def get_tags(self):
        # Tags are the labels as shown so skin and Kodi categories with the same label share a tag.
        return [xbmc.getLocalizedString(SKIN_LABEL_ID), get_label_text(self.category_label)]


class SearchResult:
    """Setting listed under a heading. Its tags are the heading tags and its search text includes them."""

    @property
    def heading(self):
        raise NotImplementedError

    @property
    def label_item(self):
        return self.heading

    def get_tags(self):
        return self.heading.tags

    @property
    def search_text(self):
        return ' '.join((self.label_text, self.description_text, *self.tags)).lower()

    def is_listed(self, level):
        """Whether the search can show the setting at the settings level."""
        return True


class SkinSearchResult(SearchResult):
    """Skin setting that keeps its skin settings behaviour. The heading of its category replaces its group."""

    @property
    def heading(self):
        return self.category


class SearchButtonSetting(SkinSearchResult, ButtonSetting):
    pass


class SearchRadioButtonSetting(SkinSearchResult, RadioButtonSetting):
    pass


class SearchSliderSetting(SkinSearchResult, SliderSetting):
    pass


class KodiSettingItem(SearchResult, SettingsListItem):
    """Control for a Kodi setting that changes its value in place, the way Kodi's settings windows do.

    The dialog reads the values of every Kodi setting when it opens and after each change.
    """

    control_id_start = KODI_SETTING_ID_START

    def __init__(self, setting, rank, heading, search):
        super().__init__(setting.key, {'label': setting.label, 'description': setting.help}, rank, heading, search)
        self.setting = setting
        self.current = get_setting_value(setting.meta)

    @property
    def heading(self):
        return self.parent

    @property
    def category(self):
        return self.parent

    @cached_property
    def editor(self):
        return get_setting_editor(self)

    @cached_property
    def value_property(self):
        return f'{PROPERTY_PREFIX}.{self.control_id}.Value'

    @property
    def value_info(self):
        return f'$INFO[Window.Property({self.value_property})]'

    @property
    def focusable_condition(self):
        return self.visible

    def is_listed(self, level):
        return self.setting.level <= level and self.current.is_enabled

    def onrefresh(self, window):
        """Values are set by the dialog when it opens because reading them on each focus change is too slow."""

    def show_value(self, window):
        window.setProperty(self.value_property, self.current.text)

    def set_value(self, window, meta):
        """Show the details Kodi gives for the setting now, or hide it when Kodi no longer shows it."""
        self.current = get_setting_value(meta) if meta else MissingValue()
        self.show_value(window)

    def onclick(self, window):
        self.editor.edit(window)


class KodiButtonSetting(KodiSettingItem):
    """Button that shows the value of the setting and opens the dialog Kodi uses to change it."""

    template = 'button'

    def get_values(self):
        return {**super().get_values(), 'label2': self.value_info}


class KodiRadioButtonSetting(KodiSettingItem):
    """Radiobutton for a setting that Kodi switches on and off with a toggle."""

    template = 'radiobutton'

    @cached_property
    def selected_property(self):
        return f'{PROPERTY_PREFIX}.{self.control_id}.Selected'

    @property
    def selected_condition(self):
        return f'!String.IsEmpty(Window.Property({self.selected_property}))'

    def get_overrides(self):
        return super().get_overrides() + [('selected', self.selected_condition, {})]

    def show_value(self, window):
        super().show_value(window)
        window.setProperty(self.selected_property, 'true' if self.current.value else '')


class KodiSliderSetting(KodiSettingItem):
    """Slider for a setting that Kodi changes with a slider. The slider positions are the steps of its range.

    Each move changes the setting. The other settings are read again once focus leaves the slider.
    """

    template = 'slider'

    def get_values(self):
        # Template text shows the value with $SUBSTITUTE[steplabel] as it does for skin sliders.
        return {**super().get_values(), 'label2': self.value_info, 'steplabel': self.value_info}

    def show_value(self, window):
        super().show_value(window)
        window.set_slider_value(self.control_id, self.current.position, self.current.maximum_position)

    def onclick(self, window):
        # Sliders send a click each time they move.
        value = self.current.steps[window.get_slider_value(self.control_id)]
        KodiSettingChange(self.setting.key, value).run()
        self.set_value(window, {**self.current.meta, 'value': value})
        window.refresh_pending = True


KODI_SETTING_CLASSES = {
    'toggle': KodiRadioButtonSetting,
    'slider': KodiSliderSetting,
}


def get_kodi_setting_item(setting, rank, heading, search):
    item_class = KODI_SETTING_CLASSES.get(setting.meta['control']['type'], KodiButtonSetting)
    return item_class(setting, rank, heading, search)
