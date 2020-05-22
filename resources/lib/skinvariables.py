# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
from json import loads
import resources.lib.utils as utils
import xml.etree.ElementTree as ET
ADDON = xbmcaddon.Addon()
XML_HEADER = '<?xml version=\"1.0\" encoding=\"UTF-8\"?>'


def make_xml_itertxt(xmltree, indent=1, indent_spaces=4, p_dialog=None):
    """
    xmltree = [{'name': '', 'tags': {'tagname': 'tagvalue'}, 'content': '' or []}]
    <{name} {tagname}="{tagvalue}">{content}</{name}>
    """
    txt = ''
    indent_str = ' ' * indent_spaces * indent

    p_total = len(xmltree) if p_dialog else 0
    p_dialog_txt = ''
    for p_count, i in enumerate(xmltree):
        if not i.get('name', ''):
            continue  # No tag name so ignore

        txt += '\n' + indent_str + '<{}'.format(i.get('name'))  # Start our tag

        for k, v in i.get('tags', {}).items():
            if not k:
                continue
            txt += ' {}=\"{}\"'.format(k, v)  # Add tag attributes
            p_dialog_txt = v

        if not i.get('content'):
            txt += '/>'
            continue  # No content so close tag and move onto next line

        txt += '>'

        if p_dialog:
            p_dialog.update((p_count * 100) // p_total, message=u'{}'.format(p_dialog_txt))

        if isinstance(i.get('content'), list):
            txt += make_xml_itertxt(i.get('content'), indent=indent + 1)
            txt += '\n' + indent_str  # Need to indent before closing tag
        else:
            txt += i.get('content')
        txt += '</{}>'.format(i.get('name'))  # Finish
    return txt


def make_xml(lines=[], p_dialog=None):
    txt = XML_HEADER
    txt += '\n<includes>'
    txt += make_xml_itertxt(lines, p_dialog=p_dialog)
    txt += '\n</includes>'
    return txt


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
            build_var['name'] = 'value'
            build_var['tags'] = {}
            for k, v in value.items():
                if not k or not v:
                    continue
                build_var['tags']['condition'] = k.format(**f_dict)
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
                build_var = {'name': 'expression' if expression else 'variable', 'tags': {}, 'content': []}

                tag_name = var_name
                tag_name += '_C{}'.format(container) if container else ''
                tag_name += '_{}'.format(listitem) if listitem or listitem == 0 else ''
                build_var['tags']['name'] = tag_name

                li_name = 'Container({}).ListItem'.format(container) if container else 'ListItem'
                li_name += '({})'.format(listitem) if listitem else ''

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
            build_var = {'name': 'variable', 'tags': {'name': var_name + '_Parent'}, 'content': []}

            content = []
            for container in containers:
                valu = var_name
                valu += '_C{}'.format(container) if container else ''
                valu = '$VAR[{}]'.format(valu)
                f_dict = {'id': container or ''}
                cond = p_var.format(**f_dict) if container else 'True'
                content.append({'name': 'value', 'tags': {'condition': cond}, 'content': valu})
            build_var['content'] = content
            skin_vars.append(build_var)
        return skin_vars

    def get_folders(self):
        folders = []
        try:
            addonfile = xbmcvfs.File('special://skin/addon.xml')
            addoncontent = addonfile.read()
        finally:
            addonfile.close()
        xmltree = ET.ElementTree(ET.fromstring(addoncontent))
        for child in xmltree.getroot():
            if child.attrib.get('point') == 'xbmc.gui.skin':
                for grandchild in child:
                    if grandchild.tag == 'res' and grandchild.attrib.get('folder'):
                        folders.append(grandchild.attrib.get('folder'))
        return folders

    def write_xml(self, folders=None, txt=None):
        if not folders or not txt:
            return
        for folder in folders:
            filepath = 'special://skin/{}/script-skinvariables-includes.xml'.format(folder)
            f = xbmcvfs.File(filepath, 'w')
            f.write(utils.try_encode_string(txt))
            f.close()
        xbmc.executebuiltin('Skin.SetString(script-skinvariables-hash,hash-{})'.format(len(self.content)))
        xbmc.executebuiltin('ReloadSkin()')

    def update_xml(self, force=False, skinfolder=None):
        if not self.meta:
            return

        if not force:  # Allow overriding over built check
            this_version = 'hash-{}'.format(len(self.content))
            last_version = xbmc.getInfoLabel('Skin.String(script-skinvariables-hash)')
            if this_version and last_version and this_version == last_version:
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
        folders = [skinfolder] if skinfolder else self.get_folders()
        self.write_xml(folders, make_xml(xmltree, p_dialog=p_dialog)) if folders else None

        p_dialog.close()
