# -*- coding: utf-8 -*-
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.shortcuts.skinshortcuts.actions import SkinShortcutsMethodsJSON, SkinShortcutsMethodsXML
from resources.lib.shortcuts.skinshortcuts.menu import SkinShortcutsMenu


class SkinShortcutsXML(SkinShortcutsMenu, SkinShortcutsMethodsXML):
    pass


class SkinShortcutsJSON(SkinShortcutsMenu, SkinShortcutsMethodsJSON):
    pass


def get_skinshortcuts_menu(route, mode='xml', **kwargs):
    factory = {'xml': SkinShortcutsXML, 'json': SkinShortcutsJSON}
    factory[mode](**kwargs).run(route)
