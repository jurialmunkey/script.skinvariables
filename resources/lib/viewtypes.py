# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
from json import loads, dumps
from jurialmunkey.parser import try_int
from jurialmunkey.futils import check_hash, make_hash, write_skinfile, write_file, load_filecontent
from jurialmunkey.jsnrpc import get_jsonrpc
from jurialmunkey.ftools import cached_property


ADDON = xbmcaddon.Addon()
ADDON_DATA = 'special://profile/addon_data/script.skinvariables/'


def join_conditions(org='', new='', operator=' | '):
    return '{}{}{}'.format(org, operator, new) if org else new


def _get_localized(text):
    if not text:
        return ''
    if text.startswith('$LOCALIZE'):
        text = text.strip('$LOCALIZE[]')
    if try_int(text):
        text = xbmc.getLocalizedString(try_int(text))
    return text


class ViewTypesItem():
    def __init__(self, viewtypes, view_id, icons=None):
        self.viewtypes = viewtypes
        self.view_id = view_id
        self.icons = icons

    @cached_property
    def name(self):
        return _get_localized(self.viewtypes.get(self.view_id))

    @cached_property
    def icon(self):
        if not self.icons:
            return ''
        return self.icons.get(self.view_id)

    @cached_property
    def item(self):
        item = xbmcgui.ListItem(label=self.name)
        item.setArt({'thumb': self.icon, 'icon': self.icon})
        return item


class ViewTypesGroup():
    def __init__(self, key, items, icon=None):
        self.key = key
        self.items = items
        self.icon = icon or ''

    @cached_property
    def name(self):
        return _get_localized(self.key)

    @cached_property
    def item(self):
        item = xbmcgui.ListItem(label=self.name)
        item.setArt({'thumb': self.icon, 'icon': self.icon})
        return item


class ViewTypesPluginGroup():
    def __init__(self, items, groups=None, header=None):
        self.items = items
        self.groups = groups
        self.header = header or ''

    def get_valid_viewtypes(self, group):
        return tuple((
            i for i in self.items
            if i.view_id in group['viewtypes']
        ))

    @cached_property
    def configured_groups(self):
        configured_groups = tuple((
            ViewTypesGroup(
                key=key,
                items=self.get_valid_viewtypes(group),
                icon=group.get('icon')
            )
            for key, group in self.groups.items()
        ))
        return tuple((i for i in configured_groups if i.items))  # Filter out empty groups for current plugin/content

    @cached_property
    def choice(self):
        from resources.lib.kodiutils import isactive_winprop
        with isactive_winprop('SkinViewtypes.DialogIsActive', reverse=True):
            choice = self.select()
        return choice

    def select(self):
        x = xbmcgui.Dialog().select(
            self.header,
            [i.item for i in self.configured_groups],
            useDetails=True,
        )
        if x == -1:
            return
        return self.configured_groups[x]


class ViewTypesPluginView():
    def __init__(self, viewtypes_obj, contentid, pluginname):
        self.viewtypes_obj = viewtypes_obj  # ViewTypes class instance
        self.contentid = contentid
        self.pluginname = pluginname

    @cached_property
    def current_viewid(self):
        try:
            return self.viewtypes_obj.addon_meta[self.pluginname][self.contentid]
        except (KeyError, TypeError):
            return

    @cached_property
    def preselect(self):
        if not self.current_viewid:
            return
        if self.current_viewid not in self.viewtype_ids:
            return
        return self.viewtype_ids.index(self.current_viewid)

    @cached_property
    def content(self):
        return self.viewtypes_obj.rules.get(self.contentid)

    @cached_property
    def content_viewtypes(self):
        return self.content.get('viewtypes') or []

    @cached_property
    def viewtype_ids(self):
        return [
            i for i in self.viewtypes_obj.viewtypes.keys()  # Resort according to base definition order of viewtypes
            if i in self.content_viewtypes  # Only include viewtype IDs that are actually defined
        ]

    @cached_property
    def items(self):
        items = tuple((
            self.get_viewtypes_item(view_id)
            for view_id in self.viewtype_ids
        ))
        if not self.viewtypes_obj.groups:
            return items
        choice = ViewTypesPluginGroup(items, self.viewtypes_obj.groups, header=self.header).choice
        return choice.items if choice else None

    def get_viewtypes_item(self, view_id):
        return ViewTypesItem(self.viewtypes_obj.viewtypes, view_id, self.viewtypes_obj.icons)

    @cached_property
    def header(self):
        return '{} {} ({})'.format(ADDON.getLocalizedString(32004), self.pluginname, self.contentid)

    @cached_property
    def choice(self):
        from resources.lib.kodiutils import isactive_winprop
        with isactive_winprop('SkinViewtypes.DialogIsActive'):
            return self.select()

    def select(self):
        if not self.items:
            return
        x = xbmcgui.Dialog().select(
            self.header,
            [i.item for i in self.items],
            useDetails=bool(self.viewtypes_obj.icons),
            preselect=self.preselect
        )
        if x != -1:
            return self.items[x]
        if not self.viewtypes_obj.groups:
            return
        return ViewTypesPluginView(self.viewtypes_obj, self.contentid, self.pluginname).select()

    @cached_property
    def view_id(self):
        if not self.contentid:
            return
        if not self.pluginname:
            return
        if not self.content:
            return
        if not self.choice:
            return
        return self.choice.view_id


class ViewTypes(object):
    def __init__(self):
        if not xbmcvfs.exists(ADDON_DATA):
            xbmcvfs.mkdir(ADDON_DATA)

    @cached_property
    def content(self):
        return load_filecontent('special://skin/shortcuts/skinviewtypes.json')

    @cached_property
    def meta(self):
        return loads(self.content) or {}

    @cached_property
    def rules(self):
        return self.meta.get('rules') or {}

    @cached_property
    def icons(self):
        return self.meta.get('icons') or {}

    @cached_property
    def viewtypes(self):
        return self.meta.get('viewtypes') or {}

    @cached_property
    def groups(self):
        return self.meta.get('groups') or {}

    @cached_property
    def addon_datafile(self):
        return f'{ADDON_DATA}{xbmc.getSkinDir()}-viewtypes.json'

    @cached_property
    def addon_content(self):
        return load_filecontent(self.addon_datafile)

    @cached_property
    def addon_meta(self):
        if not self.addon_content:
            return {}
        return loads(self.addon_content) or {}

    @cached_property
    def prefix(self):
        return self.meta.get('prefix', 'Exp_View') + '_'

    @cached_property
    def skinfolders(self):
        from resources.lib.xmlhelper import get_skinfolders
        return get_skinfolders()

    def make_defaultjson(self, overwrite=False):
        p_dialog = xbmcgui.DialogProgressBG()
        p_dialog.create(ADDON.getLocalizedString(32002), ADDON.getLocalizedString(32003))
        p_total = len(self.meta.get('rules', {}))

        addon_meta = {'library': {}, 'plugins': {}}
        for p_count, (k, v) in enumerate(self.meta.get('rules', {}).items()):
            p_dialog.update((p_count * 100) // p_total, message=u'{} {}'.format(ADDON.getLocalizedString(32005), k))
            # TODO: Add checks that file is properly configured and warn user otherwise
            addon_meta['library'][k] = v.get('library')
            addon_meta['plugins'][k] = v.get('plugins') or v.get('library')
        if overwrite:
            write_file(filepath=self.addon_datafile, content=dumps(addon_meta))

        p_dialog.close()
        return addon_meta

    def make_xmltree(self):
        """
        Build the default viewtype expressions based on json file
        """
        xmltree = []
        expressions = {}
        viewtypes = {}

        p_dialog = xbmcgui.DialogProgressBG()
        p_dialog.create(ADDON.getLocalizedString(32002), ADDON.getLocalizedString(32003))

        for v in self.meta.get('viewtypes', {}):
            expressions[v] = ''  # Construct our expressions dictionary
            viewtypes[v] = {}  # Construct our viewtypes dictionary

        # Build the definitions for each viewid
        p_dialog.update(25, message=ADDON.getLocalizedString(32006))
        for base_k, base_v in self.addon_meta.items():
            for contentid, viewid in base_v.items():
                try:
                    viewtypes_viewid = viewtypes[viewid]
                except KeyError:
                    continue
                if base_k == 'library':
                    viewtypes_viewid.setdefault(contentid, {}).setdefault('library', True)
                    continue
                if base_k == 'plugins':
                    viewtypes_viewid.setdefault(contentid, {}).setdefault('plugins', True)
                    continue
                for i in viewtypes:
                    listtype = 'whitelist' if i == viewid else 'blacklist'
                    viewtypes[i].setdefault(contentid, {}).setdefault(listtype, [])
                    viewtypes[i][contentid][listtype].append(base_k)

        # Build the visibility expression
        p_dialog.update(50, message=ADDON.getLocalizedString(32007))
        for viewid, base_v in viewtypes.items():
            for contentid, child_v in base_v.items():
                rule = self.meta.get('rules', {}).get(contentid, {}).get('rule')  # Container.Content()

                whitelist = ''
                if child_v.get('library'):
                    whitelist = 'String.IsEmpty(Container.PluginName)'
                for i in child_v.get('whitelist', []):
                    whitelist = join_conditions(whitelist, 'String.IsEqual(Container.PluginName,{})'.format(i))

                blacklist = ''
                if child_v.get('plugins'):
                    blacklist = '!String.IsEmpty(Container.PluginName)'
                    for i in child_v.get('blacklist', []):
                        blacklist = join_conditions(blacklist, '!String.IsEqual(Container.PluginName,{})'.format(i), operator=' + ')

                affix = '[{}] | [{}]'.format(whitelist, blacklist) if whitelist and blacklist else whitelist or blacklist

                if affix:
                    expression = '[{} + [{}]]'.format(rule, affix)
                    expressions[viewid] = join_conditions(expressions.get(viewid), expression)

        # Build conditional rules for disabling view lock
        if self.meta.get('condition'):
            sep = ' | '
            for viewid in self.meta.get('viewtypes', {}):
                rule = ['[{}]'.format(v.get('rule')) for k, v in self.meta.get('rules', {}).items() if viewid in v.get('viewtypes', [])]
                rule_cond = '![{}] + [{}]'.format(self.meta.get('condition'), sep.join(rule))
                rule_expr = '[{}] + [{}]'.format(self.meta.get('condition'), expressions.get(viewid))
                expressions[viewid] = '[{}] | [{}]'.format(rule_expr, rule_cond)

        # Build XMLTree
        p_dialog.update(75, message=ADDON.getLocalizedString(32008))
        for exp_name, exp_content in expressions.items():
            exp_include = 'True' if exp_content else 'False'
            exp_content = exp_content.replace('[]', '[False]') if exp_content else 'False'  # Replace None conditions with explicit False because Kodi complains about empty visibility conditions
            exp_content = '[{}]'.format(exp_content)
            xmltree.append({
                'tag': 'expression',
                'attrib': {'name': self.prefix + exp_name},
                'content': exp_content})
            xmltree.append({
                'tag': 'expression',
                'attrib': {'name': self.prefix + exp_name + '_Include'},
                'content': exp_include})

        p_dialog.close()
        return xmltree

    def add_pluginview(self, contentid=None, pluginname=None):
        view_id = ViewTypesPluginView(self, contentid, pluginname).view_id
        if not view_id:
            return
        self.addon_meta.setdefault(pluginname, {})
        self.addon_meta[pluginname][contentid] = view_id
        return view_id

    def make_xmlfile(self, skinfolder=None, hashvalue=None):
        xmltree = self.make_xmltree()

        # # Get folder to save to
        folders = [skinfolder] if skinfolder else self.skinfolders
        if folders:
            from resources.lib.xmlhelper import make_xml_includes
            write_skinfile(
                folders=folders, filename='script-skinviewtypes-includes.xml',
                content=make_xml_includes(xmltree),
                checksum='script-skinviewtypes-checksum',
                hashname='script-skinviewtypes-hash', hashvalue=hashvalue)

        write_file(filepath=self.addon_datafile, content=dumps(self.addon_meta))

    def add_newplugin(self):
        """
        Get list of available plugins and allow user to choose which to views to add
        """
        method = "Addons.GetAddons"
        properties = ["name", "thumbnail"]
        params_a = {"type": "xbmc.addon.video", "properties": properties}
        params_b = {"type": "xbmc.addon.audio", "properties": properties}
        params_c = {"type": "xbmc.addon.image", "properties": properties}
        response_a = get_jsonrpc(method, params_a).get('result', {}).get('addons') or []
        response_b = get_jsonrpc(method, params_b).get('result', {}).get('addons') or []
        response_c = get_jsonrpc(method, params_c).get('result', {}).get('addons') or []
        response = response_a + response_b + response_c
        dialog_list, dialog_ids = [], []
        for i in response:
            dialog_item = xbmcgui.ListItem(label=i.get('name'), label2='{}'.format(i.get('addonid')))
            dialog_item.setArt({'icon': i.get('thumbnail'), 'thumb': i.get('thumbnail')})
            dialog_list.append(dialog_item)
            dialog_ids.append(i.get('addonid'))
        idx = xbmcgui.Dialog().select(ADDON.getLocalizedString(32009), dialog_list, useDetails=True)
        if idx == -1:
            return
        pluginname = dialog_ids[idx]
        contentids = [i for i in sorted(self.meta.get('rules', {}))]
        idx = xbmcgui.Dialog().select(ADDON.getLocalizedString(32010), contentids)
        if idx == -1:
            return self.add_newplugin()  # Go back to previous dialog
        contentid = contentids[idx]
        return self.add_pluginview(pluginname=pluginname, contentid=contentid)

    def get_addondetails(self, addonid=None, prop=None):
        """
        Get details of a plugin
        """
        if not addonid or not prop:
            return
        method = "Addons.GetAddonDetails"
        params = {"addonid": addonid, "properties": [prop]}
        return get_jsonrpc(method, params).get('result', {}).get('addon', {}).get(prop)

    def dc_listcomp(self, listitems, listprefix='', idprefix='', contentid=''):
        return [
            ('{}{} ({})'.format(listprefix, k.capitalize(), _get_localized(self.meta.get('viewtypes', {}).get(v))), (idprefix, k))
            for k, v in listitems if not contentid or contentid == k]

    def dialog_configure(self, contentid=None, pluginname=None, viewid=None, force=False):
        dialog_list = []

        if not pluginname or pluginname == 'library':  # Build list of views for content types in library
            dialog_list += self.dc_listcomp(
                sorted(self.addon_meta.get('library', {}).items()), listprefix='Library - ', idprefix='library', contentid=contentid)

        if not pluginname or pluginname == 'plugins':  # Build list of views for content types in generic plugins
            dialog_list += self.dc_listcomp(
                sorted(self.addon_meta.get('plugins', {}).items()), listprefix='Plugins - ', idprefix='plugins', contentid=contentid)

        if not pluginname or pluginname != 'library':  # Build list of views for content types in specific plugins
            for k, v in self.addon_meta.items():
                if k in ['library', 'plugins']:  # Skip the generic library/plugin views since we already built them
                    continue
                if pluginname and pluginname != 'plugins' and pluginname != k:
                    continue  # Only add the named plugin if not just doing generic plugins
                name = self.get_addondetails(addonid=k, prop='name')
                dialog_list += self.dc_listcomp(
                    sorted(v.items()), listprefix=u'{} - '.format(name), idprefix=k, contentid=contentid)
                dialog_list.append(('Reset all {} views...'.format(name), (k, 'default')))  # Add option to reset specific plugin views

        if not contentid:  # Add options to reset all views (if configuring all content types)
            if not pluginname or pluginname == 'plugins':
                dialog_list.append((ADDON.getLocalizedString(32011).format('plugin'), ('plugins', 'default')))
            if not pluginname or pluginname == 'library':
                dialog_list.append((ADDON.getLocalizedString(32011).format('library'), ('library', 'default')))
            if not pluginname or pluginname != 'library':
                dialog_list.append((ADDON.getLocalizedString(32012), (None, 'add_pluginview')))

        idx = xbmcgui.Dialog().select(ADDON.getLocalizedString(32013), [i[0] for i in dialog_list])  # Make the dialog
        if idx == -1:
            return force  # User cancelled

        usr_pluginname, usr_contentid = dialog_list[idx][1]  # Get the selected option as a tuple
        if usr_contentid == 'default':  # If "default" then reset that section to defaults (after asking to confirm)
            choice = xbmcgui.Dialog().yesno(
                ADDON.getLocalizedString(32014).format(usr_pluginname),
                ADDON.getLocalizedString(32015).format(usr_pluginname))

            if choice and usr_pluginname == 'plugins':  # Reset all plugins views to default (both generic and specific)
                self.addon_meta[usr_pluginname] = self.make_defaultjson().get(usr_pluginname, {})  # Rebuild default views for generic plugins
                for i in self.addon_meta.copy():  # Also remove any specific plugin entries
                    self.addon_meta.pop(i) if i not in ['library', 'plugins'] else None  # Don't remove library views or the generic plugin views we just built
            elif choice and usr_pluginname == 'library':  # Reset all library views to default
                self.addon_meta[usr_pluginname] = self.make_defaultjson().get(usr_pluginname, {})
            elif choice and usr_pluginname:  # Reset a specific plugin to defaults
                self.addon_meta.pop(usr_pluginname)  # Pop the plugin entry to remove

            force = force or choice
        elif usr_contentid == 'add_pluginview':  # User wants to add a view for a specific plugin and content type
            choice = self.add_newplugin()  # Ask user to select a plugin and content type to add a view for
            force = force or choice
        else:   # Change an existing viewtype
            choice = self.add_pluginview(contentid=usr_contentid.lower(), pluginname=usr_pluginname.lower())
            force = force or choice

        return self.dialog_configure(contentid=contentid, pluginname=pluginname, viewid=viewid, force=force)  # Recursively open dialog so that user can set multiple choices

    def xmlfile_exists(self, skinfolder=None, hashname='script-skinviewtypes-checksum'):
        folders = [skinfolder] if skinfolder else self.skinfolders

        for folder in folders:
            if not xbmcvfs.exists('special://skin/{}/script-skinviewtypes-includes.xml'.format(folder)):
                return False
            content = load_filecontent('special://skin/{}/script-skinviewtypes-includes.xml'.format(folder))
            if content and check_hash(hashname, make_hash(content)):
                return False
        return True

    def update_xml(self, force=False, skinfolder=None, contentid=None, viewid=None, pluginname=None, configure=False, no_reload=False, **kwargs):
        if not self.meta:
            return

        makexml = force

        # Make these strings for simplicity
        contentid = contentid or ''
        pluginname = pluginname or ''

        # Simple hash value based on character size of file
        hashvalue = make_hash(self.content)

        if not makexml:
            makexml = check_hash('script-skinviewtypes-hash', hashvalue)

        if not self.addon_meta:
            self.addon_meta = self.make_defaultjson(overwrite=True)
        elif makexml:
            from jurialmunkey.parser import merge_dicts
            self.addon_meta = merge_dicts(self.make_defaultjson(), self.addon_meta)

        if configure:  # Configure kwparam so open gui
            makexml = self.dialog_configure(contentid=contentid.lower(), pluginname=pluginname.lower(), viewid=viewid)
        elif contentid:  # If contentid defined but no configure kwparam then just select a view
            pluginname = pluginname or 'library'
            makexml = self.add_pluginview(contentid=contentid.lower(), pluginname=pluginname.lower())

        if not makexml and self.xmlfile_exists(skinfolder):
            return

        self.make_xmlfile(skinfolder=skinfolder, hashvalue=hashvalue)

        if no_reload:
            return

        xbmc.Monitor().waitForAbort(0.4)
        xbmc.executebuiltin('ReloadSkin()')
