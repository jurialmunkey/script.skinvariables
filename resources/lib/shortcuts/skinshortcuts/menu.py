# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.shortcuts.skinshortcuts.names import MenuName, MenuConfiguration
import re
import xbmc
import xbmcgui
import xml.etree.ElementTree as ET
from json import loads
from jurialmunkey.futils import get_files_in_folder, load_filecontent
from resources.lib.kodiutils import get_localized
from resources.lib.shortcuts.skinshortcuts.storage import DATA_FOLDER, SKIN_FOLDER

get_infolabel = xbmc.getInfoLabel


class SkinShortcutsMenu():
    def __init__(self, skin, **kwargs):
        self.skin = skin
        self.params = kwargs
        self.folders = [(SKIN_FOLDER, '(.*)\\.DATA\\.xml'), (DATA_FOLDER, f'{self.skin}-(.*)\\.DATA\\.xml')]
        self.meta = self.read_skinshortcuts(self.folders)
        self.config = self.read_config()

    def read_config(self):
        content = load_filecontent('special://skin/shortcuts/skinvariables-skinshortcuts.json')
        if not content:
            return {}
        return MenuConfiguration(loads(content) or {}, self.meta).result

    @staticmethod
    def load_skinshortcut_file(filename):
        xmlstring = load_filecontent(filename)
        if not xmlstring:
            return []
        return [{i.tag: i.text for i in shortcut} for shortcut in ET.fromstring(xmlstring)]

    def load_skinshortcut(self, filename, configure_ids=True):
        meta = self.load_skinshortcut_file(filename)
        if not configure_ids:
            return meta
        return self.configure_ids(meta)

    def read_skinshortcuts(self, folders):
        files = ((folder, regex, file) for folder, regex in folders for file in get_files_in_folder(folder, regex))
        return {
            re.search(regex, file).group(1): self.load_skinshortcut(f'{folder}{file}')
            for folder, regex, file in files
        }

    def configure_ids(self, meta):
        return [self.config_id(item) for item in meta]

    @staticmethod
    def config_id(item):
        if item.get('defaultID'):
            return item
        label_id = item.get('labelID') or re.sub('[^0-9a-zA-Z]+', '', item.get('label') or '')
        item['defaultID'] = item['labelID'] = label_id.lower()
        return item

    def get_index(self, label):
        if label not in self.config:
            return ''
        if 'index' not in self.config[label]:
            return
        return str(self.config[label]['index'] or '')

    def get_nice_name(self, label):
        return MenuName(label, self.config).name

    def choose_menu(self, header, names=None):
        names = names if names else self.meta.keys()
        regex = self.params.get('label_regex')
        files = [
            (self.get_nice_name(i), i, self.get_index(i), )
            for i in names
            if not regex or re.search(regex, self.get_nice_name(i))
        ]
        files = sorted(files, key=lambda a: f'{a[2] or ""}{a[0]}')
        x = xbmcgui.Dialog().select(header, [i[0] for i in files])
        if x == -1:
            return (None, '')
        choice = [i for i in files][x]
        return (choice[1], choice[0])

    def get_menu_name(self, name=None, heading=get_localized(32029)):
        if not name:
            return
        name = [i[4:] if i.startswith('num-') else i for i in name.split('||')]
        menu = [k for k in self.meta.keys() if any(re.match(i, k) for i in name)]
        if len(menu) == 1:
            return menu[0]
        if len(menu) > 1:
            return self.choose_menu(heading, menu)[0]
        return self.choose_menu(heading)[0]

    def run(self, action):
        route = getattr(self, action)

        try:
            success = route()
        except KeyError:
            success = False

        if not success:
            return

        if self.params.get('executebuiltin'):
            xbmc.executebuiltin(self.params['executebuiltin'])
