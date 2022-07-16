# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import xbmcvfs


def make_hash(content):
    import hashlib
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def check_hash(hashname, hashvalue=None):
    last_version = xbmc.getInfoLabel('Skin.String({})'.format(hashname))
    if not last_version:
        return hashvalue
    if hashvalue != last_version:
        return hashvalue


def load_filecontent(filename=None):
    try:
        vfs_file = xbmcvfs.File(filename)
        content = vfs_file.read()
    finally:
        vfs_file.close()
    return content


def write_file(filepath=None, content=None):
    if not filepath:
        return
    f = xbmcvfs.File(filepath, 'w')
    f.write(content)
    f.close()


def write_skinfile(filename=None, folders=None, content=None, hashvalue=None, hashname=None, checksum=None):
    if not filename or not folders or not content:
        return

    for folder in folders:
        write_file(filepath='special://skin/{}/{}'.format(folder, filename), content=content)

    if hashvalue and hashname:
        xbmc.executebuiltin('Skin.SetString({},{})'.format(hashname, hashvalue))

    if checksum:
        xbmc.executebuiltin('Skin.SetString({},{})'.format(checksum, make_hash(content)))
