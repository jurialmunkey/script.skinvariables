# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import resources.lib.shortcuts.futils as shortcutfutils
from resources.lib.shortcuts.node.tree import assign_guid


def cache_meta_from_file(filepath, fileprop, refresh=False):
    meta = shortcutfutils.read_meta_from_prop(fileprop) if not refresh else None
    if meta is None:
        meta = shortcutfutils.read_meta_from_file(filepath)
        meta = assign_guid(meta)
        shortcutfutils.write_meta_to_prop(meta, fileprop)
    return meta
