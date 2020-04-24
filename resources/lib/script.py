# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sys
import xbmc
import xbmcgui
import xbmcvfs
from json import loads
import resources.lib.utils as utils


class Script(object):
    def __init__(self):
        self.home = xbmcgui.Window(10000)
        self.params = {}

    def get_params(self):
        for arg in sys.argv:
            if arg == 'script.py':
                pass
            elif '=' in arg:
                arg_split = arg.split('=', 1)
                if arg_split[0] and arg_split[1]:
                    key, value = arg_split
                    self.params.setdefault(key, value)
            else:
                self.params.setdefault(arg, True)

    def make_variables(self):
        try:
            vfs_file = xbmcvfs.File('special://skin/shortcuts/skinvariables.json')
            content = vfs_file.read()
            meta = loads(content) or []
        finally:
            vfs_file.close()

        if not self.params.get('force'):  # Allow overriding over built check
            this_version = len(content)
            last_version = utils.try_parse_int(xbmc.getInfoLabel('Skin.String(script-skinvariables-hash)'))
            if this_version and last_version and this_version == last_version:
                return  # Already updated

        if not meta:
            return

        txt = '<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<includes>'
        for variable in meta:
            v_name = variable.get('name')
            values = variable.get('values')
            if not v_name or not values:
                continue  # Skip items without names or values to make
            containers = variable.get('containers', [])
            containers.append('')
            li_a = variable.get('listitems', {}).get('start', 0)
            li_z = variable.get('listitems', {}).get('end')
            listitems = [i for i in range(li_a, int(li_z) + 1)] if li_z else []
            listitems.append('')
            for container in containers:
                for listitem in listitems:
                    txt += '\n    <variable name=\"{}'.format(v_name)
                    txt += '_C{}'.format(container) if container else ''
                    txt += '_{}'.format(listitem) if listitem or listitem == 0 else ''
                    txt += '\">'
                    for value in values:
                        for k, v in value.items():
                            if not k or not v:
                                continue
                            li_name = 'Container({}).ListItem'.format(container) if container else 'ListItem'
                            li_name += '({})'.format(listitem) if listitem else ''
                            f_dict = {
                                'listitem': li_name,
                                'listitemabsolute': li_name.replace('ListItem(', 'ListItemAbsolute('),
                                'listitemnowrap': li_name.replace('ListItem(', 'ListItemNoWrap('),
                                'listitemposition': li_name.replace('ListItem(', 'ListItemPosition(')}
                            cond = k.format(**f_dict)
                            valu = v.format(**f_dict)
                            txt += '\n        <value condition=\"{}\">{}</value>'.format(cond, valu)
                    txt += '\n    </variable>'
        txt += '\n</includes>'

        filepath = 'special://skin/{}/script-skinvariables-includes.xml'.format(self.params.get('folder', '1080i'))
        f = xbmcvfs.File(filepath, 'w')
        f.write(utils.try_encode_string(txt))
        f.close()
        xbmc.executebuiltin('ReloadSkin()')
        xbmc.executebuiltin('Skin.SetString(script-skinvariables-hash,{})'.format(len(content)))

    def router(self):
        self.make_variables()
