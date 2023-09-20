# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import re
import xbmc
import xbmcgui
import jurialmunkey.futils
import xml.etree.ElementTree as ET
from jurialmunkey.futils import get_files_in_folder, load_filecontent, write_file
# from resources.lib.kodiutils import kodi_log
ADDONDATA = 'special://profile/addon_data/script.skinvariables/'
TAB = '    '
DATA_FOLDER = 'special://profile/addon_data/script.skinshortcuts/'
SKIN_FOLDER = 'special://skin/shortcuts/'


class FileUtils(jurialmunkey.futils.FileUtils):
    addondata = ADDONDATA   # Override module addon_data with plugin addon_data


FILEUTILS = FileUtils()
delete_file = FILEUTILS.delete_file


get_infolabel = xbmc.getInfoLabel


class SkinShortcutsMenu():
    def __init__(self, skin, **kwargs):
        self.skin = skin
        self.params = kwargs
        self.meta = self.read_skinshortcuts()

    def read_skinshortcuts(self):

        folders = [
            (SKIN_FOLDER, r'(.*)\.DATA\.xml'),
            (DATA_FOLDER, fr'{self.skin}-(.*)\.DATA\.xml')
        ]

        meta = {}
        for folder, regex in folders:
            for file in get_files_in_folder(folder, regex):
                name = re.search(regex, file).group(1)
                filename = f'{folder}{file}'
                xmlstring = load_filecontent(filename)
                if not xmlstring:
                    continue
                json = [{i.tag: i.text for i in shortcut} for shortcut in ET.fromstring(xmlstring)]
                meta[name] = json

        return meta

    def write_shortcut(self, name):
        shortcuts_content = []
        for shortcut in self.meta[name]:
            shortcut_content = '\n'.join([f'{TAB}{TAB}<{tag_name}>{tag_text}</{tag_name}>' for tag_name, tag_text in shortcut.items()])
            shortcut_content = f'{TAB}<shortcut>\n{shortcut_content}\n{TAB}</shortcut>'
            shortcut_content = shortcut_content.replace('&', '&amp;')
            shortcuts_content.append(shortcut_content)
        shortcuts_content = '\n'.join(shortcuts_content)
        content = f'<shortcuts>\n{shortcuts_content}\n</shortcuts>'
        filepath = f'{DATA_FOLDER}{self.skin}-{name}.DATA.xml'
        write_file(filepath=filepath, content=content)
        delete_file(folder=DATA_FOLDER, filename=f'{self.skin}.hash', join_addon_data=False)

    @staticmethod
    def get_nice_name(label):
        affix = ''

        if label.endswith('-1'):
            affix = ' (Home Widgets)'
            label = label[:-2]

        while True:
            result = re.search(r'.*\$LOCALIZE\[(.*?)\].*', label)
            if not result:
                break
            try:
                localized = xbmc.getLocalizedString(int(result.group(1))) or ''
            except ValueError:
                localized = ''
            label = label.replace(result.group(0), localized)

        while True:
            result = re.search(r'.*\$INFO\[(.*?)\].*', label)
            if not result:
                break
            localized = get_infolabel(result.group(1)) or ''
            label = label.replace(result.group(0), localized)

        try:
            label = xbmc.getLocalizedString(int(label)) or label
        except ValueError:
            pass

        label = f'{label}{affix}'

        return label

    def choose_menu(self, header):
        files = [self.get_nice_name(i) for i in self.meta.keys()]
        x = xbmcgui.Dialog().select(header, files)
        if x == -1:
            return
        return [i for i in self.meta.keys()][x]

    def del_skinshortcut(self):
        name = self.params.get('name') or ''
        name = name[4:] if name.startswith('num-') else name
        if name not in self.meta.keys():
            name = self.choose_menu('Delete from Menu')
        if not name:
            return
        try:
            x = int(self.params.get('index')) - 1
        except (ValueError, TypeError):
            files = [self.get_nice_name(i.get('label')) for i in self.meta[name]]
            x = xbmcgui.Dialog().select('Delete from Menu', files)
        if x == -1:
            return
        self.meta[name].pop(x)
        self.write_shortcut(name)
        return name

    def add_skinshortcut(self):
        action = ''

        def _get_infolabel(infolabel):
            if self.params.get('use_listitem'):
                return get_infolabel(infolabel) or ''
            return ''

        if self.params.get('path') or self.params.get('use_listitem'):
            window = self.params.get('window') or 'videos'
            folder = self.params.get('path') or _get_infolabel('Container.ListItem.FolderPath')
            action = f"ActivateWindow({window},{folder},return)"

        item = {
            'label': self.params.get('label') or _get_infolabel('Container.ListItem.Label'),
            'label2': self.params.get('label2') or _get_infolabel('Container.ListItem.Label2'),
            'icon': self.params.get('icon') or _get_infolabel('Container.ListItem.Icon'),
            'thumb': self.params.get('thumb') or '',
            'action': action
        }

        name = self.choose_menu('Add to Menu')
        if not name:
            return
        self.meta[name].append(item)
        self.write_shortcut(name)
        return name

    def run(self, action):
        success = False
        if action == 'add_skinshortcut':
            success = self.add_skinshortcut()
        elif action == 'del_skinshortcut':
            success = self.del_skinshortcut()

        if not success:
            return

        if self.params.get('executebuiltin'):
            xbmc.executebuiltin(self.params['executebuiltin'])
