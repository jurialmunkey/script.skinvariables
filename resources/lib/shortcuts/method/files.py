# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.shortcuts.method.templates import MenuTemplate
import xbmcgui
from resources.lib.kodiutils import get_localized


def copy_menufolder(copy_menufolder, skin, force=False):
    """
    Copy every menu file in a folder over the skin's menu files
    force = skip the overwrite confirmation, e.g. when the skin has already asked the user
    """
    from jurialmunkey.parser import boolean
    from resources.lib.shortcuts.futils import read_meta_from_file, get_files_in_folder

    files = get_files_in_folder(copy_menufolder, r'.*\.json')
    if not files:
        xbmcgui.Dialog().ok(get_localized(32076), f'copy_menufolder={copy_menufolder}\nskin={skin}')
        return

    if not boolean(force):
        msg = get_localized(32072).format(
            filename=get_localized(32073).format(skin=skin),
            content=get_localized(32074).format(folder=copy_menufolder))
        msg = f'{msg}\n{get_localized(32043)}'

        x = xbmcgui.Dialog().yesno(get_localized(32075), msg)

        if not x or x == -1:
            return

    from resources.lib.shortcuts.node.tree import assign_guid
    from resources.lib.shortcuts.futils import write_meta_to_file

    files = ((read_meta_from_file(f'{copy_menufolder}{f}'), f) for f in files if f)
    for meta, file in files:
        if not meta or not file:
            continue
        write_meta_to_file(assign_guid(meta), folder=skin, filename=file, fileprop=f'{skin}-{file}', reload=True)


def copy_menufile(copy_menufile, filename, skin):
    from resources.lib.shortcuts.futils import read_meta_from_file, write_meta_to_file, FILE_PREFIX
    if not copy_menufile or not filename or not skin:
        raise ValueError(
            f'copy_menufile details missing\ncopy_menufile={copy_menufile}\nfilename={filename}\nskin={skin}',
        )
    filename = f'{FILE_PREFIX}{filename}.json'
    meta = read_meta_from_file(copy_menufile)
    if meta is None:
        raise ValueError(
            f'copy_menufile content missing\ncopy_menufile={copy_menufile}\nfilename={filename}\nskin={skin}',
        )
    x = xbmcgui.Dialog().yesno(
        get_localized(32075),
        f'{get_localized(32072).format(filename=filename, content=copy_menufile)}\n{get_localized(32043)}',
    )
    if not x or x == -1:
        return
    from resources.lib.shortcuts.node.tree import assign_guid
    write_meta_to_file(assign_guid(meta), folder=skin, filename=filename, fileprop=f'{skin}-{filename}', reload=True)


def write_menu(write_menu, skin, template, force=False, **kwargs):
    MenuTemplate(write_menu, skin, template, force, kwargs).write()
