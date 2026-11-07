# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
import re
from copy import deepcopy
from json import loads
from jurialmunkey.parser import parse_math, parse_paramstring
from jurialmunkey.futils import load_filecontent
from resources.lib.operations import check_condition
from resources.lib.shortcuts.node.lookup import get_menunode_lookup
from resources.lib.shortcuts.xmltojson import xml_to_json
from resources.lib.shortcuts.template.iteration import ListIteration, MenuIteration
from resources.lib.shortcuts.template.common import FormatDict, SKIN_BASEDIR, SHORTCUTS_FOLDER


class TemplatePart():
    def __init__(self, parent, genxml, **kwargs):
        self.skinid = parent.skinid
        self.genxml = deepcopy(genxml)
        self.params = FormatDict(kwargs)
        self.stored = parent.stored if hasattr(parent, 'stored') else {}

    @cached_property
    def is_condition(self):
        return self.get_is_condition()

    def get_is_condition(self):
        self._is_condition = self.parse_condition(self.genxml.pop('condition', []))
        return self._is_condition

    def parse_condition(self, conditions):
        conditions = conditions if isinstance(conditions, list) else [conditions]
        return all([check_condition(self.get_formatted(condition)) for condition in conditions])

    def parse_lookup(self, string):
        """ $LOOKUP[lookup_key?menu=sidemenu&filter_guid=xyz] """
        LOOKUP_REGEX = r'\$LOOKUP\[(.*?)\]'
        match = re.search(LOOKUP_REGEX, string)
        if not match:
            return string
        lookup, paramstring = match.group(1).split('?', 1)
        params = parse_paramstring(paramstring)
        output = get_menunode_lookup(lookup, skin=self.skinid, **params)
        string = string.replace(match.group(0), output)
        return self.parse_lookup(string)

    def get_formatted(self, string, params=None):
        string = string.format_map(params or self.params)
        string = parse_math(string)
        string = self.parse_lookup(string)
        return string

    def get_conditional_value(self, items):
        for i in items:
            if isinstance(i, str):
                return self.get_formatted(i)
            if self.parse_condition(i.get('condition', 'true')):
                return self.get_formatted(i['value'] or '')
        return ''

    def update_params(self):
        for k, v in self.genxml.items():
            if isinstance(v, dict):
                self.params[k] = '\n'.join(self.get_contents(v, self.params))
                continue
            if isinstance(v, list):
                self.params[k] = self.get_conditional_value(v)
                continue
            self.params[k] = self.get_formatted(v)
        return self.params

    def get_menunode(self):
        return MenuIteration(self).contents

    def get_itemlist(self):
        return ListIteration(self).contents

    def get_template(self):  # _make_template
        filelist = self.genxml.pop("template")
        filelist = filelist if isinstance(filelist, list) else [filelist]
        contents = []
        fmt_dict = self.update_params()
        for template in filelist:
            file = load_filecontent(f'{SKIN_BASEDIR}/{SHORTCUTS_FOLDER}/{template}') if template.endswith(
                '.xmltemplate',
            ) else template
            item = self.get_formatted(file, fmt_dict)
            contents.append(item)
        return ['\n'.join(contents)]

    def add_datafile(self):
        filelist = self.genxml.pop("datafile")
        filelist = filelist if isinstance(filelist, list) else [filelist]
        contents = {}
        for datafile in filelist:
            file = load_filecontent(f'{SKIN_BASEDIR}/{SHORTCUTS_FOLDER}/{datafile}')
            func = xml_to_json if datafile.endswith('.xml') else loads
            meta = func(file) if file else {}
            contents.update(meta)
        contents.update(self.genxml)
        self.genxml = contents
        return self.genxml

    def get_enumitem(self):
        enumitem = self.genxml.pop("enumitem")
        for k, v in enumitem.items():
            name = self.get_formatted(v)
            enum = self.stored.setdefault(name, 0) + 1
            self.stored[name] = enum
            self.genxml[k] = f'{enum}'
            self.params[k] = f'{enum}'
        return self.genxml

    def get_for_each(self):
        if 'list' in self.genxml:
            return self.get_itemlist()
        return self.get_menunode()

    def get_contents(self, genxml, params):
        params = params or {}
        return TemplatePart(self, genxml, **params).get_content()

    def get_content(self):  # _make_contents
        if 'datafile' in self.genxml:
            self.add_datafile()
        if not self.is_condition:
            return []
        if 'enumitem' in self.genxml:
            self.get_enumitem()
        if 'template' in self.genxml:
            return self.get_template()
        if 'for_each' in self.genxml:
            return self.get_for_each()
        return []
