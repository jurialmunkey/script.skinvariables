# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from string import ascii_lowercase
from xbmcgui import ListItem


class KeyboardKey:
    """Item in the keyboard list that changes the search text when clicked."""

    @property
    def name(self):
        raise NotImplementedError

    @property
    def label(self):
        raise NotImplementedError

    @property
    def listitem(self):
        return self.get_listitem()

    def get_listitem(self):
        listitem = ListItem(label=self.label, offscreen=True)
        listitem.setProperty('key', self.name)
        return listitem

    def apply(self, text):
        raise NotImplementedError


class CharacterKey(KeyboardKey):
    def __init__(self, character):
        self.character = character

    @property
    def name(self):
        return self.character

    @property
    def label(self):
        return self.character.upper()

    def apply(self, text):
        return f'{text}{self.character}'


class SpaceKey(CharacterKey):
    def __init__(self):
        super().__init__(' ')

    @property
    def name(self):
        return 'space'

    @property
    def label(self):
        return '_'


class BackspaceKey(KeyboardKey):
    @property
    def name(self):
        return 'backspace'

    @property
    def label(self):
        return '<'

    def apply(self, text):
        return text[:-1]


KEYBOARD_KEYS = (
    *(CharacterKey(character) for character in ascii_lowercase),
    SpaceKey(),
    BackspaceKey(),
)
