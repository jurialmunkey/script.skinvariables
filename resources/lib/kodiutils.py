# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmcgui
import tmdbhelper.logger as tmdbhelper_logger
import tmdbhelper.plugin as tmdbhelper_plugin
from contextlib import contextmanager


KODIPLUGIN = tmdbhelper_plugin.KodiPlugin('script.skinvariables')
ADDON = KODIPLUGIN._addon
get_localized = KODIPLUGIN.get_localized


LOGGER = tmdbhelper_logger.Logger(
    log_name='[script.skinvariables]\n',
    notification_head=f'SkinVariables {get_localized(257)}',
    notification_text=get_localized(2104),
    debug_logging=False)
kodi_log = LOGGER.kodi_log


@contextmanager
def isactive_winprop(name, value='True', windowid=10000):
    xbmcgui.Window(windowid).setProperty(name, value)
    try:
        yield
    finally:
        xbmcgui.Window(windowid).clearProperty(name)
