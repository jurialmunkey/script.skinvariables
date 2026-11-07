# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.jsnrpc import set_tags


def set_dbid_tag(set_dbid_tag, dbtype, dbid, **kwargs):
    set_tags(int(dbid), dbtype, [set_dbid_tag])
