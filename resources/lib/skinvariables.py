# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import xbmcgui
import xbmcaddon
from json import loads
import resources.lib.utils as utils


ADDON = xbmcaddon.Addon()


class SkinVariables(object):
    def __init__(self):
        self.content = utils.load_filecontent('special://skin/shortcuts/skinvariables.json')
        self.meta = loads(self.content) or []

    def build_containers(self, variable={}):
        containers = variable.get('containers', [])
        containers.append('')
        return containers

    def build_listitems(self, variable={}):
        li_a = variable.get('listitems', {}).get('start', 0)
        li_z = variable.get('listitems', {}).get('end')
        listitems = [i for i in range(li_a, int(li_z) + 1)] if li_z else []
        listitems.append('')
        return listitems

    def get_contentvalues(self, values, f_dict):
        content = []
        for value in values:
            build_var = {}
            build_var['tag'] = 'value'
            build_var['attrib'] = {}
            for k, v in value.items():
                if not k or not v:
                    continue
                build_var['attrib']['condition'] = k.format(**f_dict)
                build_var['content'] = v.format(**f_dict)
            content.append(build_var)
        return content

    def get_skinvariable(self, variable, expression=False):
        if not variable:
            return

        var_name = variable.get('name')

        if not var_name:
            return

        containers = self.build_containers(variable)
        listitems = self.build_listitems(variable)
        values = variable.get('values', [])
        skin_vars = []

        for container in containers:
            # Build Variables for each ListItem Position in Container
            for listitem in listitems:
                build_var = {'tag': 'expression' if expression else 'variable', 'attrib': {}, 'content': []}

                tag_name = var_name
                tag_name += '_C{}'.format(container) if container else ''
                tag_name += '_{}'.format(listitem) if listitem or listitem == 0 else ''
                build_var['attrib']['name'] = tag_name

                li_name = 'Container({}).ListItem'.format(container) if container else 'ListItem'
                li_name += '({})'.format(listitem) if listitem or listitem == 0 else ''

                f_dict = {
                    'id': container or '',
                    'pos': listitem or 0,
                    'listitem': li_name,
                    'listitemabsolute': li_name.replace('ListItem(', 'ListItemAbsolute('),
                    'listitemnowrap': li_name.replace('ListItem(', 'ListItemNoWrap('),
                    'listitemposition': li_name.replace('ListItem(', 'ListItemPosition(')}

                build_var['content'] = variable.get('expression', '').format(**f_dict) if expression else self.get_contentvalues(values, f_dict)
                skin_vars.append(build_var)

        # Build variable for parent containers
        if variable.get('parent'):
            p_var = variable.get('parent')
            build_var = {'tag': 'variable', 'attrib': {'name': var_name + '_Parent'}, 'content': []}

            content = []
            for container in containers:
                valu = var_name
                valu += '_C{}'.format(container) if container else ''
                valu = '$VAR[{}]'.format(valu)
                f_dict = {'id': container or ''}
                cond = p_var.format(**f_dict) if container else 'True'
                content.append({'tag': 'value', 'attrib': {'condition': cond}, 'content': valu})
            build_var['content'] = content
            skin_vars.append(build_var)
        return skin_vars

    def update_xml(self, force=False, skinfolder=None):
        if not self.meta:
            return

        hashvalue = 'hash-{}'.format(len(self.content))

        if not force:  # Allow overriding over built check
            last_version = xbmc.getInfoLabel('Skin.String(script-skinvariables-hash)')
            if hashvalue and last_version and hashvalue == last_version:
                return  # Already updated

        p_dialog = xbmcgui.DialogProgressBG()
        p_dialog.create(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32000))

        xmltree = []
        for i in self.meta:
            item = None
            if i.get('values'):
                item = self.get_skinvariable(i)
            elif i.get('expression'):
                item = self.get_skinvariable(i, expression=True)
            xmltree = xmltree + item if item else xmltree

        # Get folder to save to
        folders = [skinfolder] if skinfolder else utils.get_skinfolders()
        if folders:
            utils.write_skinfile(
                folders=folders, filename='script-skinvariables-includes.xml',
                content=utils.make_xml_includes(xmltree, p_dialog=p_dialog),
                hashvalue=hashvalue, hashname='script-skinvariables-hash')

        p_dialog.close()
