# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc


class SettingAction:
    """Builtin of a setting definition. Actions without a condition always run.

    Buttons give it to the skin as an onclick while the script runs it for other controls.
    """

    def __init__(self, meta):
        self.meta = meta

    @property
    def action(self):
        return self.meta['action']

    @property
    def condition(self):
        return self.meta.get('condition', '')

    @property
    def is_active(self):
        return not self.condition or xbmc.getCondVisibility(self.condition)

    @property
    def override(self):
        attrib = {'condition': self.condition} if self.condition else {}
        return ('onclick', self.action, attrib)

    def run(self):
        # Conditions are checked as each action runs so they see the changes made by earlier actions.
        if not self.is_active:
            return
        # Waiting lets later conditions and the setting state see the changes made by this action.
        xbmc.executebuiltin(self.action, True)
