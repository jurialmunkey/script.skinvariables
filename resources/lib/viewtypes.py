# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
from json import loads, dumps
import resources.lib.utils as utils


ADDON = xbmcaddon.Addon()
ADDON_DATA = 'special://profile/addon_data/script.skinvariables/'


class ViewTypes(object):
    def __init__(self):
        self.content = utils.load_filecontent('special://skin/shortcuts/skinviewtypes.json')
        self.meta = loads(self.content) or []
        if not xbmcvfs.exists(ADDON_DATA):
            xbmcvfs.mkdir(ADDON_DATA)
        self.addon_datafile = ADDON_DATA + xbmc.getSkinDir() + '-viewtypes.json'
        self.addon_content = utils.load_filecontent(self.addon_datafile)
        self.addon_meta = loads(self.addon_content) or {} if self.addon_content else {}
        self.prefix = self.meta.get('prefix', 'Exp_View') + '_'

    def make_defaultjson(self, overwrite=True):
        addon_meta = {'library': {}, 'plugins': {}}
        for k, v in self.meta.get('rules', {}).items():
            # TODO: Add checks that file is properly configured and warn user otherwise
            addon_meta['library'][k] = v.get('library')
            addon_meta['plugins'][k] = v.get('plugins') or v.get('library')
        if overwrite:
            utils.write_file(filepath=self.addon_datafile, content=dumps(addon_meta))
        return addon_meta

    def make_xmltree(self):
        """
        Build the default viewtype expressions based on json file
        """
        xmltree = []
        expressions = {}
        viewtypes = {}

        for v in self.meta.get('viewtypes', {}):
            expressions[v] = ''  # Construct our expressions dictionary
            viewtypes[v] = {}  # Construct our viewtypes dictionary

        # Build the definitions for each viewid
        for base_k, base_v in self.addon_meta.items():
            for contentid, viewid in base_v.items():
                if base_k == 'library':
                    viewtypes[viewid].setdefault(contentid, {}).setdefault('library', True)
                    continue
                if base_k == 'plugins':
                    viewtypes[viewid].setdefault(contentid, {}).setdefault('plugins', True)
                    continue
                for i in viewtypes:
                    listtype = 'whitelist' if i == viewid else 'blacklist'
                    viewtypes[i].setdefault(contentid, {}).setdefault(listtype, [])
                    viewtypes[i][contentid][listtype].append(base_k)

        # Construct the visibility expression
        for viewid, base_v in viewtypes.items():
            for contentid, child_v in base_v.items():
                rule = self.meta.get('rules', {}).get(contentid, {}).get('rule')  # Container.Content()

                whitelist = ''
                if child_v.get('library'):
                    whitelist = 'String.IsEmpty(Container.PluginName)'
                for i in child_v.get('whitelist', []):
                    whitelist = utils.join_conditions(whitelist, 'String.IsEqual(Container.PluginName,{})'.format(i))

                blacklist = ''
                if child_v.get('plugins'):
                    blacklist = '!String.IsEmpty(Container.PluginName)'
                    for i in child_v.get('blacklist', []):
                        blacklist = utils.join_conditions(blacklist, '!String.IsEqual(Container.PluginName,{})'.format(i), operator=' + ')

                affix = '[{}] | [{}]'.format(whitelist, blacklist) if whitelist and blacklist else whitelist or blacklist

                if affix:
                    expression = '[{} + [{}]]'.format(rule, affix)
                    expressions[viewid] = utils.join_conditions(expressions.get(viewid), expression)

        # Construct XMLTree
        for exp_name, exp_content in expressions.items():
            xmltree.append({
                'tag': 'expression',
                'attrib': {'name': self.prefix + exp_name},
                'content': '[{}]'.format(exp_content)})

        return xmltree

    def add_pluginview(self, contentid=None, pluginname=None, viewid=None, overwrite=True):
        if not contentid or not pluginname or not self.meta.get('rules', {}).get(contentid):
            return
        if not viewid:
            items, ids = [], []
            for i in self.meta.get('rules', {}).get(contentid, {}).get('viewtypes', []):
                ids.append(i)
                items.append(self.meta.get('viewtypes', {}).get(i))
            header = '{} {} ({})'.format(ADDON.getLocalizedString(32004), pluginname, contentid)
            choice = xbmcgui.Dialog().select(header, items)
            viewid = ids[choice] if choice != -1 else None
        if not viewid:
            return  # No viewtype chosen
        self.addon_meta.setdefault(pluginname, {})
        self.addon_meta[pluginname][contentid] = viewid
        if overwrite:
            utils.write_file(filepath=self.addon_datafile, content=dumps(self.addon_meta))
        return viewid

    def update_xml(self, force=False, skinfolder=None, contentid=None, viewid=None, pluginname=None):
        if not self.meta:
            return

        hashvalue = 'hash-{}'.format(len(self.content))

        with utils.busy_dialog():
            if not force:
                last_version = xbmc.getInfoLabel('Skin.String(script-skinviewtypes-hash)')
                if not last_version or hashvalue != last_version:
                    force = True
            if force:
                self.addon_meta = self.make_defaultjson()

        if contentid:
            pluginname = pluginname or 'library'
            force = self.add_pluginview(contentid=contentid.lower(), pluginname=pluginname.lower(), viewid=viewid)

        if not force:
            return

        with utils.busy_dialog():
            xmltree = self.make_xmltree()

            # # Get folder to save to
            folders = [skinfolder] if skinfolder else utils.get_skinfolders()
            if folders:
                utils.write_skinfile(
                    folders=folders, filename='script-skinviewtypes-includes.xml',
                    content=utils.make_xml_includes(xmltree),
                    hashname='script-skinviewtypes-hash', hashvalue=hashvalue)
