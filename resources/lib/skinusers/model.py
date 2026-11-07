# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import random
import re
from jurialmunkey.ftools import cached_property
from jurialmunkey.parser import boolean
from resources.lib.kodiutils import get_localized


class SkinUser:
    def __init__(self, meta):
        self.meta = meta

    @property
    def name(self):
        return self.meta.get('name')

    @property
    def slug(self):
        return self.meta.get('slug')

    @property
    def icon(self):
        return self.meta.get('icon', '')

    @property
    def code(self):
        return self.meta.get('code')

    @property
    def has_menu(self):
        return self.get_has_menu()

    def get_has_menu(self):
        return boolean(self.meta.get('menu', True))


class DefaultSkinUser(SkinUser):
    def __init__(self):
        super().__init__({'name': get_localized(32061), 'slug': 'default'})


class NewSkinUser:
    def __init__(self, name, code):
        self.name = name
        self.code = code

    @cached_property
    def slug(self):
        return self.get_slug()

    def get_slug(self):
        slug = re.sub('[^0-9a-zA-Z]+', '', self.name)
        slug = slug or f'{random.randrange(16**8):08x}'
        # Prefix numeric names so Kodi does not interpret them as localization IDs.
        return f'user-{slug}'

    @cached_property
    def meta(self):
        return self.get_meta()

    def get_meta(self):
        return {'name': self.name, 'slug': self.slug, 'icon': '', 'code': self.code}
