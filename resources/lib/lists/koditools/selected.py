# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from jurialmunkey.litems import ContainerDirectory
from resources.lib.lists.koditools.common import WindowProperties
from resources.lib.lists.labelgetter import ListInfoLabelGetter


class SelectedItem:
    def __init__(self, container, infolabels, artwork, separator='/', listitem='ListItem(0)'):
        self.getter = ListInfoLabelGetter(container)
        self.infolabels = infolabels
        self.artwork_names = artwork
        self.separator = separator
        self.listitem = listitem

    def get_infolabel(self, key):
        return self.getter.get_infolabel(f'{self.listitem}.{key}')

    @cached_property
    def label(self):
        return self.get_label()

    def get_label(self):
        return self.get_infolabel('Label')

    @cached_property
    def properties(self):
        return self.get_properties()

    def get_properties(self):
        return {key: self.get_infolabel(key) for key in self.infolabels.split(self.separator)}

    @cached_property
    def artwork(self):
        return self.get_artwork()

    def get_artwork(self):
        return {key: self.get_infolabel(f'Art({key})') for key in self.artwork_names.split(self.separator)}

    @cached_property
    def item(self):
        return self.get_item()

    def get_item(self):
        label = self.label
        properties = self.properties
        artwork = self.artwork
        item = ContainerDirectory.get_list_item(label)
        item[1].setProperties(properties)
        item[1].setArt(artwork)
        return item


class ListGetSelectedItem(ContainerDirectory):
    def get_directory(
        self,
        container,
        infolabels='',
        artwork='',
        separator='/',
        listitem='ListItem(0)',
        window_prop=None,
        window_id=None,
        **kwargs,
    ):
        if not container:
            return
        result = SelectedItem(container, infolabels, artwork, separator, listitem)
        self.add_items([result.item])
        if window_prop:
            properties = WindowProperties(window_prop, window_id)
            properties.set_values(result.properties)
            properties.set_values(result.artwork)
