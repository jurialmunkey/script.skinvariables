# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
import resources.lib.shortcuts.futils as shortcutfutils
from jurialmunkey.parser import boolean
from resources.lib.shortcuts.node.constants import FILE_PREFIX
from resources.lib.shortcuts.node.tree import get_menuguid, get_menunode, get_nodename


class NodeProperties():
    @cached_property
    def fileprop(self):
        return self.get_fileprop()

    def get_fileprop(self):
        if not self.skin or not self.filename:
            return
        return f'{self.skin}-{self.filename}'

    @cached_property
    def filepath(self):
        return self.get_filepath()

    def get_filepath(self):
        if not self.skin or not self.filename:
            return
        return f'{shortcutfutils.ADDON_DATA}{self.skin}/{self.filename}'

    @cached_property
    def filename(self):
        return self.get_filename()

    def get_filename(self):
        if not self.menu:
            return
        return shortcutfutils.validify_filename(f'{FILE_PREFIX}{self.menu}.json')

    @property
    def meta(self):
        try:
            return self._meta
        except AttributeError:
            if not self.filepath:
                return
            meta = self.get_meta(self.refresh)
            if not meta:
                return
            self._meta = meta
            return self._meta

    @property
    def menunode(self):
        try:
            return self._menunode
        except AttributeError:
            self._menunode, self.node, self.name = get_menuguid(self.meta, self.guid, self.mode) or get_menunode(
                self.meta,
                self.node,
                self.mode,
            )
            return self._menunode

    @cached_property
    def nodename(self):
        return self.get_nodename()

    def get_nodename(self):
        return get_nodename(self.node)

    @property
    def node(self):
        return self._node

    @node.setter
    def node(self, value):
        try:
            self._node = tuple([int(i) for i in value.split('.') if i])
        except (TypeError, AttributeError):
            self._node = tuple()

    @property
    def mode(self):
        try:
            return self._mode or 'submenu'
        except AttributeError:
            self._mode = 'submenu'
            return self._mode

    @mode.setter
    def mode(self, value):
        self._mode = value

    @property
    def edit(self):
        try:
            return self._edit
        except AttributeError:
            self._edit = False
            return self._edit

    @edit.setter
    def edit(self, value):
        self._edit = boolean(value)
