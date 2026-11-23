# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import re
from itertools import count, takewhile
from jurialmunkey.ftools import cached_property
from resources.lib.kodiutils import get_localized


PLUGIN_LABEL_PROPERTY = 'contextmenulabel({})'
PLUGIN_ACTION_PROPERTY = 'contextmenuaction({})'
CONTAINER_UPDATE = re.compile(
    r'\s*Container\.Update\(\s*(?:"(?P<quoted>(?:[^"\\]|\\.)+)"|(?P<plain>[^,"]+?))\s*(?:,.*)?\)\s*',
    re.IGNORECASE,
)
PLAYABLE_FOLDER_PREFIXES = ('videodb://', 'library://video/')
INFO_MEDIATYPES = (
    'movie',
    'tvshow',
    'season',
    'episode',
    'musicvideo',
    'artist',
    'album',
    'song',
)


class ResultMenuEntry:
    """Entry of the context menu of a search result."""

    label_id = 0

    def __init__(self, result):
        self.result = result

    @cached_property
    def label(self):
        return self.get_label()

    def get_label(self):
        return get_localized(self.label_id)

    @property
    def is_shown(self):
        return self.get_is_shown()

    def get_is_shown(self):
        return True

    def run(self, window, opened_result):
        raise NotImplementedError


class BuiltinMenuEntry(ResultMenuEntry):
    """Entry that runs a builtin. Focus returns to the result if the builtin opens another window."""

    @cached_property
    def builtin(self):
        return self.get_builtin()

    def get_builtin(self):
        return self.result.builtin

    def run(self, window, opened_result):
        window.run_result_builtin(self.builtin, opened_result)


class BrowseMenuEntry(BuiltinMenuEntry):
    label_id = 37015

    def get_is_shown(self):
        return self.result.item.is_folder


class PlayMenuEntry(BuiltinMenuEntry):
    label_id = 208

    def get_is_shown(self):
        return not self.result.item.is_folder


class PlayFolderMenuEntry(BuiltinMenuEntry):
    """Plays a video library folder. Kodi does not offer Play on plugin folders."""

    label_id = 208

    def get_is_shown(self):
        return self.result.item.is_folder and self.result.item.path.lower().startswith(PLAYABLE_FOLDER_PREFIXES)

    def get_builtin(self):
        return f'PlayMedia("{self.result.item.path}",isdir)'


class InfoMenuEntry(ResultMenuEntry):
    label_id = 19033

    def get_is_shown(self):
        return self.result.item.mediatype in INFO_MEDIATYPES

    def run(self, window, opened_result):
        window.show_result_info(self.result)


class PluginMenuEntry(BuiltinMenuEntry):
    """Entry the plugin added to its listitem."""

    def __init__(self, result, label, action):
        super().__init__(result)
        self.plugin_label = label
        self.action = action

    def get_label(self):
        return self.plugin_label

    def get_builtin(self):
        return self.action


class ContainerUpdateMenuEntry(PluginMenuEntry):
    """Plugin entry that updates the container. Script windows drop Container.Update so its path opens in the target
    window of the source instead.
    """

    def __init__(self, result, label, action, path):
        super().__init__(result, label, action)
        self.path = path

    def get_builtin(self):
        return f'ActivateWindow({self.result.source.target},"{self.path}",return)'


class PluginMenuEntries:
    """Entries a plugin added to a result. Kodi reads them in order and stops at the first missing label."""

    def __init__(self, result):
        self.result = result

    @property
    def properties(self):
        return self.result.item.infoproperties

    def has_label(self, index):
        return PLUGIN_LABEL_PROPERTY.format(index) in self.properties

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        return [self.get_entry(index) for index in takewhile(self.has_label, count())]

    def get_entry(self, index):
        label = self.properties[PLUGIN_LABEL_PROPERTY.format(index)]
        action = self.properties.get(PLUGIN_ACTION_PROPERTY.format(index), '')
        match = CONTAINER_UPDATE.fullmatch(action)
        if match:
            return ContainerUpdateMenuEntry(self.result, label, action, match['quoted'] or match['plain'])
        return PluginMenuEntry(self.result, label, action)


class ResultContextMenu:
    """Context menu of a search result, with the plugin entries first as in Kodi's own menu."""

    core_entry_classes = (
        BrowseMenuEntry,
        PlayMenuEntry,
        PlayFolderMenuEntry,
        InfoMenuEntry,
    )

    def __init__(self, result):
        self.result = result

    @cached_property
    def plugin_entries(self):
        return PluginMenuEntries(self.result).items

    @cached_property
    def core_entries(self):
        return self.get_core_entries()

    def get_core_entries(self):
        entries = (entry_class(self.result) for entry_class in self.core_entry_classes)
        return [entry for entry in entries if entry.is_shown]

    @cached_property
    def entries(self):
        return [*self.plugin_entries, *self.core_entries]

    @cached_property
    def labels(self):
        return [entry.label for entry in self.entries]
