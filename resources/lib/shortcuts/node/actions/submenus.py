# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.shortcuts.node.submenus import SubmenuDialog


class NodeSubmenuMethods():
    def do_submenu_item(self, mode='submenu'):
        x = int(self.item)
        from resources.lib.shortcuts.browser import GetDirectoryBrowser
        from jurialmunkey.window import WindowProperty
        with WindowProperty(('IsSkinShortcut', 'True')):
            item = GetDirectoryBrowser().get_directory()
        if not item:
            return
        self.get_menunode_item(x).setdefault(mode, []).append(item)
        self.write_meta_to_file()

    def do_widgets_item(self):
        self.do_submenu_item('widgets')

    def do_submenu(self, mode='submenu'):
        return SubmenuDialog(self, mode).run()

    def do_widgets(self):
        return self.do_submenu(mode='widgets')
