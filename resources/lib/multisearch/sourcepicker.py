# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmcgui
from jurialmunkey.ftools import cached_property
from resources.lib.kodiutils import get_localized
from resources.lib.multisearch.constants import PROPERTY_PREFIX


SOURCES_ENABLED_PROPERTY = f'{PROPERTY_PREFIX}.Sources.Enabled'
SOURCES_TOTAL_PROPERTY = f'{PROPERTY_PREFIX}.Sources.Total'
SOURCES_LABEL_PROPERTY = f'{PROPERTY_PREFIX}.Sources.Label'


class SourcesPicker:
    """Dialog of the sources button that chooses which sources are searched. Any of the sources can be enabled.

    The skin builds the sources button label from the enabled count, total count and label properties.
    """

    def __init__(self, sources):
        self.sources = sources

    @cached_property
    def heading(self):
        return get_localized(39031)

    @cached_property
    def all_label(self):
        return get_localized(593)

    @property
    def label(self):
        """All while every source is enabled, otherwise the labels of the enabled sources."""
        return self.get_label()

    def get_label(self):
        if self.sources.all_enabled:
            return self.all_label
        return ', '.join(source.label for source in self.sources.enabled)

    @property
    def properties(self):
        return self.get_properties()

    def get_properties(self):
        return {
            SOURCES_ENABLED_PROPERTY: str(len(self.sources.enabled_positions)),
            SOURCES_TOTAL_PROPERTY: str(len(self.sources.items)),
            SOURCES_LABEL_PROPERTY: self.label,
        }

    def pick(self):
        """Positions of the sources chosen to be enabled. None when cancelled or when every source was turned off,
        which keeps the sources already enabled.
        """
        positions = xbmcgui.Dialog().multiselect(
            self.heading,
            self.sources.listitems,
            preselect=self.sources.enabled_positions,
        )
        return positions or None


class SingleSourcePicker(SourcesPicker):
    """Dialog that chooses between searching every source and searching one source, for windows with a list for each
    content type.
    """

    @property
    def all_listitem(self):
        return xbmcgui.ListItem(label=self.all_label, offscreen=True)

    @property
    def listitems(self):
        """All is listed first, followed by each source."""
        return [self.all_listitem, *self.sources.listitems]

    @property
    def preselect(self):
        return self.get_preselect()

    def get_preselect(self):
        if self.sources.all_enabled:
            return 0
        return self.sources.enabled_positions[0] + 1

    @property
    def all_positions(self):
        return list(range(len(self.sources.items)))

    def get_positions(self, position):
        """Every source for All, otherwise the chosen source."""
        if position == 0:
            return self.all_positions
        return [position - 1]

    def pick(self):
        position = xbmcgui.Dialog().select(
            self.heading,
            self.listitems,
            preselect=self.preselect,
        )
        if position < 0:
            return None
        return self.get_positions(position)
