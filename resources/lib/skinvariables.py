# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import xbmcgui
import xbmcaddon
from json import loads, dumps
import xml.etree.ElementTree as ET
from tmdbhelper.parser import try_int, del_empty_keys
from resources.lib.xmlhelper import make_xml_includes, get_skinfolders
from tmdbhelper.futils import load_filecontent, write_skinfile, make_hash

ADDON = xbmcaddon.Addon()


class SkinVariables(object):
    def __init__(self, template: str = None, skinfolder: str = None):
        self.template = f"skinvariables-{template}" if template else 'skinvariables'
        self.filename = f'script-{self.template}-includes.xml'
        self.hashname = f'script-{self.template}-hash'
        self.folders = [skinfolder] if skinfolder else get_skinfolders()
        self.content = self.build_json(f'special://skin/shortcuts/{self.template}.xml')
        self.content = self.content or load_filecontent(f'special://skin/shortcuts/{self.template}.json')
        self.meta = loads(self.content) or []

    def build_json(self, file):
        xmlstring = load_filecontent(file)
        if not xmlstring:
            return

        json = []
        for variable in ET.fromstring(xmlstring):
            if not variable.attrib.get('name'):
                continue  # No name specified so skip
            if variable.tag not in ['expression', 'variable']:
                continue  # Not an expression or variable so skip

            item = {}

            if variable.tag == 'expression' and variable.text:
                item['expression'] = variable.text
            elif variable.tag == 'variable':
                item['values'] = [{i.attrib.get('condition') or 'True': i.text} for i in variable if i.text]

            if not item.get('expression') and not item.get('values'):
                continue  # No values or expression so skip

            item['name'] = variable.attrib.get('name')
            item['containers'] = [
                j for i in variable.attrib.get('containers', '').split(',') for j
                in (range(*(int(y) + x for x, y, in enumerate(i.split('...')))) if '...' in i else (int(i),))]
            item['listitems'] = {}
            item['listitems']['start'] = try_int(variable.attrib.get('start'))
            item['listitems']['end'] = try_int(variable.attrib.get('end'))
            item['parent'] = variable.attrib.get('parent')

            json.append(del_empty_keys(item))

        return dumps(json)

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
                    'cid': '_C{}'.format(container) if container else '',
                    'lid': '_{}'.format(listitem) if listitem or listitem == 0 else '',
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

    def update_xml(self, force=False, no_reload=False, **kwargs):
        if not self.meta:
            return

        hashvalue = make_hash(self.content)

        if not force:  # Allow overriding over built check
            last_version = xbmc.getInfoLabel(f'Skin.String({self.hashname})')
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

        # Save to folder
        if self.folders:
            write_skinfile(
                folders=self.folders, filename=self.filename,
                content=make_xml_includes(xmltree, p_dialog=p_dialog),
                hashvalue=hashvalue, hashname=self.hashname)

        p_dialog.close()
        xbmc.executebuiltin('ReloadSkin()') if not no_reload else None
