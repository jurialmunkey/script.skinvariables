# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import re
import xbmc


COMMAND_PATTERN = re.compile(r'\$COMMAND\[(\w+)\]')


class SettingAction:
    """Action of a setting definition. Actions without a condition always run."""

    is_command = False

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

    def execute(self, window, setting):
        raise NotImplementedError

    def run(self, window, setting):
        # Conditions are checked as each action runs so they see the changes made by earlier actions.
        if not self.is_active:
            return
        self.execute(window, setting)


class BuiltinAction(SettingAction):
    """Kodi builtin. Buttons give it to the skin as an onclick while the script runs it for other controls."""

    @property
    def override(self):
        attrib = {'condition': self.condition} if self.condition else {}
        return ('onclick', self.action, attrib)

    def execute(self, window, setting):
        # Waiting lets later conditions and the setting state see the changes made by this action.
        xbmc.executebuiltin(self.action, True)


class SettingCommand(SettingAction):
    """Internal command written as $COMMAND[name] in place of a builtin. The script runs it."""

    is_command = True


class ReloadCommand(SettingCommand):
    """Reloads the skin then reopens the settings with the same view and focus on the setting."""

    def execute(self, window, setting):
        window.reload(setting.control_id)


COMMANDS = {
    'reload': ReloadCommand,
}


def get_setting_action(meta):
    command = COMMAND_PATTERN.fullmatch(meta['action'])
    return COMMANDS[command.group(1)](meta) if command else BuiltinAction(meta)
