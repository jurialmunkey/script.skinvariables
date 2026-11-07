# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import load_filecontent, make_hash
from resources.lib.operations import RuleOperations


class TemplateBuild:
    def __init__(self, template, genxml, params, force=False):
        self.template = template
        self.genxml = genxml
        self.params = params
        self.force = force
        self.initial_hash = self.current_hash

    @cached_property
    def hashinput(self):
        return self.get_hashinput()

    def get_hashinput(self):
        return '_'.join(
            [
                '_'.join(f'{key}.{value}' for key, value in self.params.items()),
                str(self.genxml),
                str(self.template.contents),
                self.template.profilename,
            ]
        )

    @property
    def current_hash(self):
        return self.get_current_hash()

    def get_current_hash(self):
        return make_hash(f'{self.hashinput}--{load_filecontent(self.template.filepath)}')

    @cached_property
    def updated(self):
        return self.get_updated()

    def get_updated(self):
        if self.force or not self.initial_hash:
            return
        last_version = xbmc.getInfoLabel(f'Skin.String({self.template.hashname})')
        return True if last_version and last_version == self.initial_hash else None

    @cached_property
    def extra_parts(self):
        return self.get_extra_parts()

    def get_extra_parts(self):
        if not self.genxml:
            return []
        return [
            {key: value for part in item.split('|') for key, value in (part.split('='),)}
            for item in self.genxml.split('||')
        ]

    def prepare(self):
        meta = self.template.meta
        meta['genxml'] += self.extra_parts
        meta['getnfo'] = {key: xbmc.getInfoLabel(value) for key, value in meta.get('getnfo', {}).items()}
        meta['getnfo'].update(self.params)
        if 'addnfo' in meta:
            meta['getnfo'].update(RuleOperations(meta['addnfo'], **meta['getnfo']).params)
