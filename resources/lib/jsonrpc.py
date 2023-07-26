# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.kodiutils import kodi_log
import jurialmunkey.jsnrpc as jurialmunkey_jsnrpc


def get_jsonrpc(method=None, params=None):
    return jurialmunkey_jsnrpc.get_jsonrpc(method, params, 1, kodi_log)
