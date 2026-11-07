# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from xbmcgui import Dialog
from jurialmunkey.ftools import cached_property
from resources.lib.methods.builtins import run_executebuiltin


class FocusSelectDialog:
    def __init__(self, container, header='', preselect_executebuiltin=None):
        self.container = container
        self.header = header
        self.preselect_executebuiltin = preselect_executebuiltin

    def get_infolabel(self, label):
        return xbmc.getInfoLabel(f'Container({self.container}).{label}')

    @cached_property
    def options(self):
        return self.get_options()

    def get_options(self):
        return [
            self.get_infolabel(f'ListItemAbsolute({index}).Label')
            for index in range(int(self.get_infolabel('NumItems') or 0))
        ]

    @property
    def preselect(self):
        return self.get_preselect()

    def get_preselect(self):
        return int(self.get_infolabel('CurrentItem')) - 1

    def run(self):
        options = self.options
        preselect = self.preselect
        index = Dialog().select(self.header, options, preselect=preselect)
        if index == -1:
            return
        if self.preselect_executebuiltin and index == preselect:
            run_executebuiltin(self.preselect_executebuiltin)
            return
        xbmc.executebuiltin(f'SetFocus({self.container},{index},absolute)')


def run_selectfocusdialog(run_selectfocusdialog, preselect_executebuiltin=None, header='', **kwargs):
    FocusSelectDialog(run_selectfocusdialog, header, preselect_executebuiltin).run()
