# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import xbmcaddon
from jurialmunkey.parser import try_int


ADDON = xbmcaddon.Addon()
ADDON_DATA = 'special://profile/addon_data/script.skinvariables/'


def join_conditions(org='', new='', operator=' | '):
    return '{}{}{}'.format(org, operator, new) if org else new


def get_localized(text):
    if not text:
        return ''
    if text.startswith('$LOCALIZE'):
        text = text.strip('$LOCALIZE[]')
    if try_int(text):
        text = xbmc.getLocalizedString(try_int(text))
    return text
