# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xml.etree.ElementTree as ET
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import load_filecontent
from jurialmunkey.jsnrpc import get_jsonrpc


# Setting levels in Kodi's order. Kodi stores the level of its settings windows as the position.
SETTING_LEVELS = ('basic', 'standard', 'advanced', 'expert')
STANDARD_LEVEL = 1
# Settings are read at the highest level so the search can show any level without reading them again.
READ_LEVEL = SETTING_LEVELS[-1]
SECTION_WINDOWS = {
    'player': 'PlayerSettings',
    'media': 'MediaSettings',
    'pvr': 'PVRSettings',
    'services': 'ServiceSettings',
    'games': 'GameSettings',
    'system': 'SystemSettings',
    'interface': 'InterfaceSettings',
}
# Settings that make Kodi reload the skin when they change. Kodi also reloads it for a new language.
RELOADING_SETTINGS = (
    'lookandfeel.skin',
    'lookandfeel.font',
    'lookandfeel.skintheme',
    'lookandfeel.skincolors',
    'locale.language',
)


class KodiSettingLevel:
    """Settings level of Kodi's settings windows. Kodi saves it to its settings file as soon as it changes."""

    filepath = 'special://profile/guisettings.xml'

    @cached_property
    def rank(self):
        return self.get_rank()

    def get_rank(self):
        # Kodi uses the standard level until the level is first changed and saved.
        root = ET.fromstring(str(load_filecontent(self.filepath)))
        return int(root.findtext('general/settinglevel', STANDARD_LEVEL))


class KodiSettingValues:
    """Current details of the settings that Kodi shows, by setting id."""

    @cached_property
    def settings(self):
        return self.get_settings()

    def get_settings(self):
        response = get_jsonrpc('Settings.GetSettings', {'level': READ_LEVEL})
        return {meta['id']: meta for meta in response['result']['settings']}


class KodiSettingChange:
    """New value for a Kodi setting. Kodi runs the same checks and callbacks as its settings windows."""

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def run(self):
        get_jsonrpc('Settings.SetSettingValue', {'setting': self.key, 'value': self.value})

    def apply(self, window):
        """Change the setting while the settings search stays open and show the settings as Kodi now has them."""
        self.run()
        window.refresh_after_change()


class KodiAddons:
    """Enabled add-ons of a type, sorted by name, as the choices of a setting that selects an add-on."""

    def __init__(self, addon_type):
        self.addon_type = addon_type

    @cached_property
    def addons(self):
        return self.get_addons()

    def get_addons(self):
        params = {'type': self.addon_type, 'enabled': True, 'properties': ['name']}
        response = get_jsonrpc('Addons.GetAddons', params)
        # Kodi leaves out the add-ons list when no add-on of the type is enabled.
        return sorted(response['result'].get('addons', []), key=lambda addon: addon['name'].casefold())

    @property
    def choices(self):
        return [(addon['name'], addon['addonid']) for addon in self.addons]


class KodiSetting:
    """Setting shown in a category of Kodi's settings windows."""

    def __init__(self, meta, category):
        self.meta = meta
        self.category = category

    @property
    def key(self):
        return self.meta['id']

    @property
    def label(self):
        return self.meta['label']

    @property
    def help(self):
        # Kodi only gives help text for settings that have it.
        return self.meta.get('help', '')

    @property
    def level(self):
        return SETTING_LEVELS.index(self.meta['level'])

    @property
    def window(self):
        return self.category.section.window

    @property
    def is_reloading(self):
        return self.key in RELOADING_SETTINGS


class KodiSettingsCategory:
    """Category of a settings window. Kodi lists its settings in groups that the search does not show."""

    def __init__(self, meta, section):
        self.meta = meta
        self.section = section

    @property
    def key(self):
        return self.meta['id']

    @property
    def label(self):
        return self.meta['label']

    @cached_property
    def settings(self):
        return self.get_settings()

    def get_settings(self):
        return [
            KodiSetting(meta, self)
            for group in self.meta['groups']
            for meta in group['settings']
        ]


class KodiSettingsSection:
    """Section of Kodi's settings shown by one settings window."""

    def __init__(self, meta):
        self.meta = meta

    @property
    def key(self):
        return self.meta['id']

    @property
    def label(self):
        return self.meta['label']

    @property
    def window(self):
        return SECTION_WINDOWS[self.key]

    @cached_property
    def categories(self):
        return self.get_categories()

    def get_categories(self):
        params = {'section': self.key, 'level': READ_LEVEL, 'properties': ['settings']}
        response = get_jsonrpc('Settings.GetCategories', params)
        return [KodiSettingsCategory(meta, self) for meta in response['result']['categories']]


class KodiSettingsTree:
    """Sections, categories and settings of Kodi's settings windows in the order the windows show them."""

    @cached_property
    def sections(self):
        return self.get_sections()

    def get_sections(self):
        response = get_jsonrpc('Settings.GetSections', {'level': READ_LEVEL})
        return [KodiSettingsSection(meta) for meta in response['result']['sections']]

    @cached_property
    def categories(self):
        return self.get_categories()

    def get_categories(self):
        return [
            category
            for section in self.sections
            for category in section.categories
        ]
