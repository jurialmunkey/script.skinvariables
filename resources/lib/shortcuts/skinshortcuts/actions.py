# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.shortcuts.skinshortcuts.items import ShortcutItem, ShortcutXML
import re
import xbmc
import xbmcgui
from jurialmunkey.futils import get_files_in_folder, write_file
from resources.lib.kodiutils import get_localized
from resources.lib.shortcuts.skinshortcuts.storage import DATA_FOLDER, delete_file

get_infolabel = xbmc.getInfoLabel


class SkinShortcutsMethodsJSON():
    pass


class SkinShortcutsMethodsXML():
    def write_shortcut(self, name):
        content = ShortcutXML(self.meta[name]).content
        write_file(filepath=f'{DATA_FOLDER}{self.skin}-{name}.DATA.xml', content=content)
        delete_file(folder=DATA_FOLDER, filename=f'{self.skin}.hash', join_addon_data=False)

    def mod_skinshortcut(self):
        name = self.get_menu_name(self.params.get('name'), heading=get_localized(32016))
        if not name:
            return
        if name[-2:-1] == '-':
            name = name[:-2] + '.' + name[-1:]
        xbmc.executebuiltin(f'RunScript(script.skinshortcuts,type=manage&group={name})')
        return name

    def del_skinshortcut(self):
        name = self.get_menu_name(self.params.get('name'), heading=get_localized(32017))
        if not name:
            return
        try:
            x = int(self.params.get('index')) - 1
        except (ValueError, TypeError):
            files = [self.get_nice_name(i.get('label')) for i in self.meta[name]]
            x = xbmcgui.Dialog().select(get_localized(117), files)
        if x == -1:
            return
        self.meta[name].pop(x)
        self.write_shortcut(name)
        return name

    def add_skinshortcut(self):
        item = self.config_id(ShortcutItem(self.params).result)
        name, nice_name = self.choose_menu(get_localized(32021))
        if not name:
            return
        self.meta[name].append(item)
        self.write_shortcut(name)
        xbmcgui.Dialog().ok(get_localized(32020), get_localized(32018).format(item.get('label') or '', nice_name))
        return name

    def imp_skinshortcut(self):
        files = [i for i in get_files_in_folder(DATA_FOLDER, r'.*?-(.*)\.DATA\.xml')]
        if not files:
            xbmcgui.Dialog().ok(get_localized(32019), get_localized(32022))
            return
        x = xbmcgui.Dialog().select(get_localized(32019), files)
        if x == -1:
            return

        name, nice_name = self.choose_menu(get_localized(32023))
        if not name:
            return
        self.meta[name] = self.load_skinshortcut(f'{DATA_FOLDER}{files[x]}')
        self.write_shortcut(name)

        xbmcgui.Dialog().ok(get_localized(32024), get_localized(32025).format(files[x], nice_name))
        return name

    def mov_skinshortcut(self):
        regex = r'(.*)\.DATA\.xml'
        folder = self.params['folder']

        if not xbmcgui.Dialog().yesno(
            get_localized(32026),
            get_localized(32027),
            yeslabel=get_localized(186),
            nolabel=get_localized(222),
        ):
            return

        for file in get_files_in_folder(folder, regex):
            name = re.search(regex, file).group(1)
            self.meta[name] = self.load_skinshortcut(f'{folder}{file}')
            self.write_shortcut(name)

        xbmcgui.Dialog().ok(get_localized(32019), get_localized(32028).format(folder, self.skin))
        return name
