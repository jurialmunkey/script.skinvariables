# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import ListItem, Dialog, INPUT_NUMERIC
from jurialmunkey.litems import Container
import jurialmunkey.futils as jmfutils


BASEPLUGIN = 'plugin://script.skinvariables/'
BASEFOLDER = 'special://profile/addon_data/script.skinvariables/logins/'
USERS_FILE = 'skinusers.json'


class FileUtils(jmfutils.FileUtils):
    addondata = BASEFOLDER   # Override module addon_data with plugin addon_data


class ListAddSkinUser(Container):
    def get_directory(self, skinid, **kwargs):
        import re
        import random
        from jurialmunkey.futils import load_filecontent
        from json import loads
        filepath = f'{BASEFOLDER}/{skinid}/{USERS_FILE}'
        file = load_filecontent(filepath)
        meta = loads(file) if file else []

        name = Dialog().input('Enter profile name')
        if not name:
            return

        slug = re.sub('[^0-9a-zA-Z]+', '', name)
        if not slug:
            slug = f'{random.randrange(16**8):08x}'  # Assign a random 32bit hex value if no valid slug name
        slug = f'user-{slug}'  # Avoid Kodi trying to localize slugs which are only numbers by adding alpha prefix

        icon = ''

        def _get_code():
            if not Dialog().yesno('Pin code lock', 'Do you want to add a pin code lock for this profile?'):
                return
            code = Dialog().input('Enter pin code', type=INPUT_NUMERIC)
            if not code:
                return
            if not Dialog().input('Re-enter pin code', type=INPUT_NUMERIC) == code:
                return _get_code()
            return str(code)

        code = _get_code()

        item = {
            'name': name,
            'slug': slug,
            'icon': icon,
            'code': code
        }

        meta.append(item)
        FileUtils().dumps_to_file(meta, folder=skinid, filename=USERS_FILE, indent=4)
        self.params['info'] = 'get_skin_user'
        ListGetSkinUser(self.handle, self.paramstring, **self.params).get_directory(**self.params)


class ListGetSkinUser(Container):
    def get_directory(self, skinid, folder, slug=None, allow_new=False, **kwargs):
        from jurialmunkey.futils import load_filecontent, write_skinfile
        from json import loads

        filepath = f'{BASEFOLDER}/{skinid}/{USERS_FILE}'
        file = load_filecontent(filepath)
        meta = loads(file) if file else []

        def _login_user():
            import xbmc
            user = next(i for i in meta if slug == i.get('slug'))

            if user.get('code') and str(user.get('code')) != str(Dialog().input('Enter pin code', type=INPUT_NUMERIC)):
                Dialog().ok('Wrong pin code!', 'Incorrect pin code entered')
                return

            filename = 'script-skinvariables-skinusers.xml'
            content = load_filecontent(f'special://skin/shortcuts/skinvariables-skinusers.xmltemplate')
            content = content.format(slug=slug, **kwargs)
            write_skinfile(folders=[folder], filename=filename, content=content)

            xbmc.executebuiltin(f'Skin.SetString(SkinVariables.SkinUser.Name,{user.get("name")})')
            xbmc.executebuiltin(f'Skin.SetString(SkinVariables.SkinUser,{slug})')
            xbmc.executebuiltin('SetProperty(SkinVariables.SkinUserLogin,True,Home)')
            xbmc.executebuiltin('ReloadSkin()')

        def _make_item(i):
            name = i.get('name') or ''
            slug = i.get('slug') or ''

            if not name or not slug:
                return

            icon = i.get('icon') or ''
            code = i.get('code') or ''
            path = f'{BASEPLUGIN}?info=get_skin_user&skinid={skinid}&slug={slug}'
            path = f'{path}&folder={folder}' if folder else path

            li = ListItem(label=name, label2=slug, path=path)
            li.setProperty('slug', slug)
            li.setProperty('code', code) if code else None
            li.setArt({'thumb': icon, 'icon': icon}) if icon else None

            return (path, li, False)

        def _join_item():
            from jurialmunkey.parser import boolean
            if not boolean(allow_new):
                return []
            name = 'Add new user...'
            path = f'{BASEPLUGIN}?info=add_skin_user&skinid={skinid}'
            path = f'{path}&folder={folder}' if folder else path
            li = ListItem(label=name, path=path)
            return [(path, li, False)]

        def _open_directory():
            items = [j for j in (_make_item(i) for i in meta) if j] + _join_item()
            plugin_category = ''
            container_content = ''
            self.add_items(items, container_content=container_content, plugin_category=plugin_category)

        _login_user() if slug else _open_directory()
