# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import re
import xbmc
from jurialmunkey.ftools import cached_property


class MenuName:
    def __init__(self, label, config):
        self.label = label
        self.config = config

    @cached_property
    def settings(self):
        return self.get_settings()

    def get_settings(self):
        return self.config[self.label] if self.label in self.config else {}

    @cached_property
    def base(self):
        return self.get_base()

    def get_base(self):
        label = self.settings.get('name') or self.label
        affix = self.settings.get('affix') or ''
        return label[:-len(affix)] if affix and label.endswith(affix) else label

    def localize(self, label):
        monitor = xbmc.Monitor()
        while not monitor.abortRequested():
            result = re.search(r'.*\$LOCALIZE\[(.*?)\].*', label)
            if not result:
                break
            try:
                localized = xbmc.getLocalizedString(int(result.group(1))) or ''
            except ValueError:
                localized = ''
            label = label.replace(result.group(0), localized)
        return label

    def resolve_info(self, label):
        monitor = xbmc.Monitor()
        while not monitor.abortRequested():
            result = re.search(r'.*\$INFO\[(.*?)\].*', label)
            if not result:
                break
            label = label.replace(result.group(0), xbmc.getInfoLabel(result.group(1)) or '')
        return label

    @cached_property
    def localized(self):
        return self.get_localized()

    def get_localized(self):
        label = self.resolve_info(self.localize(self.base))
        try:
            return xbmc.getLocalizedString(int(label)) or label
        except ValueError:
            return label

    @cached_property
    def name(self):
        return self.get_name()

    def get_name(self):
        prefix = self.settings.get('prefix') or ''
        suffix = self.settings.get('suffix') or ''
        return f'{prefix}{self.localized}{suffix}'


class MenuConfiguration:
    def __init__(self, config, menus):
        self.config = config
        self.menus = menus

    def configure_level(self, item, level):
        name = f'{item.get("defaultID")}{level.get("affix") or ""}'
        self.menus.setdefault(name, [])
        self.config.setdefault(name, dict(level))
        if item.get('label') and not item['label'].startswith('$SKIN'):
            self.config[name]['name'] = item['label']

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        levels = self.config.get('mainmenu', {}).get('levels') or [{}]
        mainmenu = self.menus.setdefault('mainmenu', [])
        for item, level in ((item, level) for item in mainmenu for level in levels):
            self.configure_level(item, level)
        return self.config
