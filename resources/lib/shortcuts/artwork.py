# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import re
from jurialmunkey.ftools import cached_property


IMAGE_REGEX = r'image://(.*)/'
ARTWORK_PREFERENCE = ['poster', 'thumb', 'icon', 'landscape', 'fanart']


class DirectoryArtwork:
    def __init__(self, artwork, definitions):
        self.artwork = artwork
        self.definitions = definitions

    @cached_property
    def preferred(self):
        return self.get_preferred()

    def get_preferred(self):
        return next((self.artwork[key] for key in ARTWORK_PREFERENCE if self.artwork.get(key)), '')

    @cached_property
    def thumbnail(self):
        return self.get_thumbnail()

    def get_thumbnail(self):
        thumb = self.preferred or self.artwork.get('thumb') or ''
        if thumb.startswith('image://Default'):
            match = re.search(IMAGE_REGEX, thumb)
            thumb = match.group(1) if match else thumb
            thumb = self.definitions.setdefault('icons', {}).get(thumb) or thumb
            thumb = f'special://skin/media/{thumb}' if thumb.startswith('Default') else thumb
        thumb = thumb or 'special://skin/media/DefaultFolder.png'
        return self.definitions.setdefault('icons', {}).get(thumb.replace('special://skin/media/', '')) or thumb

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        self.artwork['thumb'] = self.thumbnail
        return self.artwork
