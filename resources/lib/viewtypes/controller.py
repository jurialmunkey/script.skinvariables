# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from json import loads, dumps
from xbmcgui import DialogProgressBG
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import check_hash, make_hash
from jurialmunkey.parser import merge_dicts
from resources.lib.viewtypes.addons import AddonDetails, NewPluginDialog
from resources.lib.viewtypes.common import ADDON
from resources.lib.viewtypes.configuration import ViewTypesConfiguration
from resources.lib.viewtypes.expressions import ViewTypeAssignments, ViewTypeExpressions, ViewTypesXML
from resources.lib.viewtypes.menu import ConfiguredViews
from resources.lib.viewtypes.metadata import ViewTypesDefaults, ViewTypesPreferences
from resources.lib.viewtypes.selection import ViewTypesPluginView
from resources.lib.viewtypes.storage import ViewTypesStorage


class ViewTypes:
    def __init__(self):
        self.storage = ViewTypesStorage()

    @cached_property
    def content(self):
        return self.get_content()

    def get_content(self):
        return self.storage.read_template()

    @cached_property
    def meta(self):
        return self.get_meta()

    def get_meta(self):
        return loads(self.content) or {}

    @cached_property
    def rules(self):
        return self.get_rules()

    def get_rules(self):
        return self.meta.get('rules') or {}

    @cached_property
    def icons(self):
        return self.get_icons()

    def get_icons(self):
        return self.meta.get('icons') or {}

    @cached_property
    def viewtypes(self):
        return self.get_viewtypes()

    def get_viewtypes(self):
        return self.meta.get('viewtypes') or {}

    @cached_property
    def groups(self):
        return self.get_groups()

    def get_groups(self):
        return self.meta.get('groups') or {}

    @cached_property
    def addon_datafile(self):
        return self.get_addon_datafile()

    def get_addon_datafile(self):
        return self.storage.addon_datafile

    @cached_property
    def addon_content(self):
        return self.get_addon_content()

    def get_addon_content(self):
        return self.storage.read_preferences(self.addon_datafile)

    @cached_property
    def addon_meta(self):
        return self.get_addon_meta()

    def get_addon_meta(self):
        if not self.addon_content:
            return {}
        return self.validate_addon_meta(loads(self.addon_content) or {})

    def validate_addon_meta(self, meta):
        return ViewTypesPreferences(meta, self.rules, self.addon_meta_defaultjson).result

    def validate_addon_meta_rules(self, location, rules):
        return ViewTypesPreferences({}, self.rules, {}).get_valid_rules(rules)

    def is_valid_rule(self, contentid, viewid):
        return ViewTypesPreferences({}, self.rules, {}).is_valid_rule(contentid, viewid)

    @cached_property
    def addon_meta_defaultjson(self):
        return self.make_defaultjson()

    @property
    def addon_meta_content(self):
        return self.get_addon_meta_content()

    def get_addon_meta_content(self):
        return dumps(self.validate_addon_meta(self.addon_meta))

    @cached_property
    def prefix(self):
        return self.get_prefix()

    def get_prefix(self):
        return self.meta.get('prefix', 'Exp_View') + '_'

    @cached_property
    def skinfolders(self):
        return self.get_skinfolders()

    def get_skinfolders(self):
        return self.storage.skinfolders

    def make_defaultjson(self):
        return ViewTypesDefaults(self.meta.get('rules', {})).result

    def make_xmltree(self):
        progress = DialogProgressBG()
        progress.create(ADDON.getLocalizedString(32002), ADDON.getLocalizedString(32003))
        try:
            progress.update(25, message=ADDON.getLocalizedString(32006))
            assignments = ViewTypeAssignments(self.meta.get('viewtypes', {}), self.addon_meta).result
            progress.update(50, message=ADDON.getLocalizedString(32007))
            expressions = ViewTypeExpressions(self.meta, assignments).result
            progress.update(75, message=ADDON.getLocalizedString(32008))
            if not expressions:
                return []
            return ViewTypesXML(expressions, self.prefix).xmltree
        finally:
            progress.close()

    def add_pluginview(self, contentid=None, pluginname=None):
        view_id = ViewTypesPluginView(self, contentid, pluginname).view_id
        if not view_id:
            return
        self.addon_meta.setdefault(pluginname, {})[contentid] = view_id
        return view_id

    def make_xmlfile(self, skinfolder=None, hashvalue=None):
        xmltree = self.make_xmltree()
        folders = [skinfolder] if skinfolder else self.skinfolders
        if folders:
            self.storage.write_xml(folders, xmltree, hashvalue)
        self.storage.save_preferences(self.addon_datafile, self.addon_meta_content)

    def add_newplugin(self):
        return NewPluginDialog(self).run()

    def get_addondetails(self, addonid=None, prop=None):
        return AddonDetails(addonid, prop).value

    def dc_listcomp(self, listitems, listprefix='', idprefix='', contentid=''):
        return ConfiguredViews(listitems, self.meta.get('viewtypes', {}), listprefix, idprefix, contentid).entries

    def dialog_configure(self, contentid=None, pluginname=None, viewid=None, force=False):
        return ViewTypesConfiguration(self, contentid, pluginname).run(force)

    def xmlfile_exists(self, skinfolder=None, hashname='script-skinviewtypes-checksum'):
        folders = [skinfolder] if skinfolder else self.skinfolders
        return self.storage.xmlfile_exists(folders, hashname)

    def prepare_preferences(self, makexml):
        if not self.addon_meta:
            self.addon_meta = self.make_defaultjson()
            self.storage.save_preferences(self.addon_datafile, dumps(self.addon_meta))
        elif makexml:
            self.addon_meta = merge_dicts(self.addon_meta_defaultjson, self.addon_meta)

    def update_xml(
        self,
        force=False,
        skinfolder=None,
        contentid=None,
        viewid=None,
        pluginname=None,
        configure=False,
        no_reload=False,
        **kwargs,
    ):
        if not self.meta:
            return
        contentid = contentid or ''
        pluginname = pluginname or ''
        hashvalue = make_hash(self.content)
        makexml = force or check_hash('script-skinviewtypes-hash', hashvalue)
        self.prepare_preferences(makexml)
        if configure:
            makexml = self.dialog_configure(contentid=contentid.lower(), pluginname=pluginname.lower(), viewid=viewid)
        elif contentid:
            pluginname = pluginname or 'library'
            makexml = self.add_pluginview(contentid=contentid.lower(), pluginname=pluginname.lower())
        if not makexml and self.xmlfile_exists(skinfolder):
            return
        self.make_xmlfile(skinfolder=skinfolder, hashvalue=hashvalue)
        if no_reload:
            return
        xbmc.Monitor().waitForAbort(0.4)
        xbmc.executebuiltin('ReloadSkin()')
