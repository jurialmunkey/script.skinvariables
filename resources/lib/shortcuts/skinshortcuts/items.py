# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from jurialmunkey.ftools import cached_property
from resources.lib.shortcuts.skinshortcuts.storage import TAB


class ShortcutItem:
    def __init__(self, params):
        self.params = params

    def get_infolabel(self, label):
        return (xbmc.getInfoLabel(label) or '') if self.params.get('use_listitem') else ''

    @cached_property
    def action(self):
        return self.get_action()

    def get_action(self):
        if not self.params.get('path') and not self.params.get('use_listitem'):
            return ''
        window = self.params.get('window') or 'videos'
        folder = self.params.get('path') or self.get_infolabel('Container.ListItem.FolderPath')
        return f'ActivateWindow({window},{folder},return)'

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        action = self.action
        return {
            'label': self.params.get('label') or self.get_infolabel('Container.ListItem.Label'),
            'label2': self.params.get('label2') or self.get_infolabel('Container.ListItem.Label2'),
            'icon': self.params.get('icon') or self.get_infolabel('Container.ListItem.Icon'),
            'thumb': self.params.get('thumb') or '',
            'action': action,
        }


class ShortcutXML:
    def __init__(self, items):
        self.items = items

    def get_item(self, item):
        content = '\n'.join(f'{TAB}{TAB}<{tag}>{text}</{tag}>' for tag, text in item.items())
        return f'{TAB}<shortcut>\n{content}\n{TAB}</shortcut>'.replace('&', '&amp;')

    @cached_property
    def content(self):
        return self.get_content()

    def get_content(self):
        content = '\n'.join(self.get_item(item) for item in self.items)
        return f'<shortcuts>\n{content}\n</shortcuts>'
