# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.kodiutils import get_localized
from resources.lib.shortcuts.template.common import escape_ampersands, pretty_xmlcontent
from resources.lib.shortcuts.template.part import TemplatePart


class TemplateDocument:
    def __init__(self, template):
        self.template = template
        self.meta = template.meta

    @cached_property
    def globals(self):
        return self.get_globals()

    def get_globals(self):
        params = {**self.meta['getnfo']}
        params.update(
            {
                key: TemplatePart(self.template, value, **self.meta['getnfo']).get_template()[0]
                for key, value in self.meta.get('global', {}).items()
            }
        )
        return params

    @cached_property
    def parts(self):
        return self.get_parts()

    def get_parts(self):
        params = self.globals
        self.template.p_dialog.update(message=f'{get_localized(32047)}...')
        content = [self.meta['header']] if 'header' in self.meta else []
        content += [
            text
            for definition in self.meta['genxml']
            for text in TemplatePart(self.template, definition, **params).get_content()
        ]
        return content + ([self.meta['footer']] if 'footer' in self.meta else [])

    @cached_property
    def content(self):
        return self.get_content()

    def get_content(self):
        self.template.p_dialog.update(message=f'{get_localized(32046)}...')
        content = '\n'.join(self.parts)
        self.template.p_dialog.update(message=f'{get_localized(32048)}...')
        return pretty_xmlcontent(escape_ampersands(content))
