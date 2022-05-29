# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import xbmcgui
import xbmcaddon
from contextlib import contextmanager
from urllib.parse import unquote_plus


ADDON = xbmcaddon.Addon('script.skinvariables')
ADDONLOGNAME = '[script.skinvariables]\n'


def kodi_log(value, level=0):
    try:
        if isinstance(value, list):
            value = ''.join(map(str, value))
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        logvalue = u'{0}{1}'.format(ADDONLOGNAME, value)
        if level == 1:
            xbmc.log(logvalue, level=xbmc.LOGINFO)
        else:
            xbmc.log(logvalue, level=xbmc.LOGDEBUG)
    except Exception as exc:
        xbmc.log(u'Logging Error: {}'.format(exc), level=xbmc.LOGINFO)


def parse_paramstring(paramstring):
    """ helper to assist to standardise urllib parsing """
    params = dict()
    paramstring = paramstring.replace('&amp;', '&')  # Just in case xml string
    for param in paramstring.split('&'):
        if '=' not in param:
            continue
        k, v = param.split('=')
        params[unquote_plus(k)] = unquote_plus(v)
    return params


def try_int(string, base=None, fallback=0):
    '''helper to parse int from string without erroring on empty or misformed string'''
    try:
        return int(string, base) if base else int(string)
    except Exception:
        return fallback


@contextmanager
def isactive_winprop(name, value='True', windowid=10000):
    xbmcgui.Window(windowid).setProperty(name, value)
    try:
        yield
    finally:
        xbmcgui.Window(windowid).clearProperty(name)


def del_empty_keys(d, values=[]):
    my_dict = d.copy()
    for k, v in d.items():
        if not v or v in values:
            del my_dict[k]
    return my_dict


def merge_dicts(org, upd, skipempty=False):
    source = org.copy()
    for k, v in upd.items():
        if not k:
            continue
        if skipempty and not v:
            continue
        if isinstance(v, dict):
            if not isinstance(source.get(k), dict):
                source[k] = {}
            source[k] = merge_dicts(source.get(k), v, skipempty=skipempty)
            continue
        source[k] = v
    return source
