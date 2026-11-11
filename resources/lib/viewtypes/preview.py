# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from itertools import islice
from xbmcgui import ListItem
from infotagger.listitem import ListItemInfoTag
from jurialmunkey.ftools import cached_property
from resources.lib.lists.labelgetter import ListInfoLabelGetter, ListItemInfoLabelGetter
from resources.lib.viewtypes.windowitems import PROPERTY_PREFIX


PREVIEW_LIMIT = 14
# Optional skin list that always gets a copy of the focused item so skins can show its details anywhere.
FOCUSED_LIST_ID = '5000'
PREVIEW_PROPERTY_PREFIX = f'{PROPERTY_PREFIX}.ListItem'
PREVIEW_LABELS = {
    'label': 'Label',
    'label2': 'Label2',
}
PREVIEW_INFOLABELS = {
    'title': 'Title',
    'tvshowtitle': 'TVShowTitle',
    'year': 'Year',
    'premiered': 'Premiered',
    'plot': 'Plot',
    'mediatype': 'DBType',
}
PREVIEW_ART = {
    'poster': 'Art(poster)',
    'landscape': 'Art(landscape)',
    'fanart': 'Art(fanart)',
    'discart': 'Art(discart)',
    'thumb': 'Art(thumb)',
    'icon': 'Icon',
}


class PreviewContainerItem:
    """Item at an offset from the focused item in the container of the window under the selector dialog."""

    def __init__(self, offset):
        self.offset = offset

    @cached_property
    def getter(self):
        return ListItemInfoLabelGetter(0, self.offset)

    def get_infolabel(self, infolabel):
        return self.getter.get_infolabel(infolabel)

    def get_condition(self, condition):
        return xbmc.getCondVisibility(f'{self.getter.container}{self.getter.listitem}{condition}')

    @cached_property
    def is_parent_folder(self):
        return self.get_condition('IsParentFolder')

    @cached_property
    def infolabels(self):
        return self.get_infolabels()

    def get_infolabels(self):
        infolabels = {key: self.get_infolabel(name) for key, name in PREVIEW_INFOLABELS.items()}
        return {key: value for key, value in infolabels.items() if value}

    @cached_property
    def art(self):
        return self.get_art()

    def get_art(self):
        art = {key: self.get_infolabel(name) for key, name in PREVIEW_ART.items()}
        return {key: value for key, value in art.items() if value}

    @cached_property
    def labels(self):
        return self.get_labels()

    def get_labels(self):
        return {key: self.get_infolabel(name) for key, name in PREVIEW_LABELS.items()}

    @cached_property
    def properties(self):
        """Window properties named after the infolabels they were read from. Empty values are skipped."""
        return self.get_properties()

    def get_properties(self):
        values = {
            **{PREVIEW_LABELS[key]: value for key, value in self.labels.items()},
            **{PREVIEW_INFOLABELS[key]: value for key, value in self.infolabels.items()},
            **{PREVIEW_ART[key]: value for key, value in self.art.items()},
        }
        return {f'{PREVIEW_PROPERTY_PREFIX}.{name}': value for name, value in values.items() if value}

    def get_listitem(self):
        """New ListItem for each list. Kodi keeps the rendered layout on the item, so lists must not share items."""
        listitem = ListItem(**self.labels, offscreen=True)
        listitem.setArt(self.art)
        ListItemInfoTag(listitem, 'video', type_check=True).set_info(self.infolabels)
        return listitem


class PreviewFocusedItem(PreviewContainerItem):
    """The focused item, ListItem(0). Also keeps the folder path of folders.

    Skins can fill another list from the folder path to preview the contents of the focused folder.
    """

    def __init__(self):
        super().__init__(0)

    @cached_property
    def is_folder(self):
        return self.get_condition('IsFolder')

    @cached_property
    def folderpath(self):
        return self.get_folderpath()

    def get_folderpath(self):
        if not self.is_folder:
            return ''
        return self.get_infolabel('FolderPath')

    def get_properties(self):
        properties = super().get_properties()
        if self.folderpath:
            properties[f'{PREVIEW_PROPERTY_PREFIX}.FolderPath'] = self.folderpath
        return properties

    def get_listitem(self):
        listitem = super().get_listitem()
        if self.folderpath:
            listitem.setPath(self.folderpath)
            listitem.setIsFolder(True)
        return listitem


class PreviewContainer:
    """Items read from the focused item onwards in the container of the window under the selector dialog.

    ListItem(offset) wraps around the container so offsets up to the item count read each item once.
    The parent folder item is skipped.
    """

    def __init__(self, limit):
        self.limit = limit

    @cached_property
    def numallitems(self):
        return int(ListInfoLabelGetter(0).get_infolabel('NumAllItems') or 0)

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        items = (PreviewContainerItem(offset) for offset in range(self.numallitems))
        return tuple(islice((item for item in items if not item.is_parent_folder), self.limit))


class ViewTypesPreviews:
    """Preview ListItems by list id for the skin lists with viewtype ids, limited per list, and the focused list."""

    def __init__(self, limits, focused_list=False):
        self.limits = limits
        self.focused_list = focused_list

    @cached_property
    def focused_item(self):
        return PreviewFocusedItem()

    @cached_property
    def properties(self):
        """Window properties for the focused item. Set whether or not the skin has preview lists."""
        return self.focused_item.properties

    @cached_property
    def container(self):
        """Read once for the longest list so the shorter lists reuse the same infolabels."""
        return PreviewContainer(max(self.limits.values(), default=0))

    @cached_property
    def view_previews(self):
        return self.get_view_previews()

    def get_view_previews(self):
        return {
            view_id: tuple(item.get_listitem() for item in self.container.items[:limit])
            for view_id, limit in self.limits.items()
        }

    @cached_property
    def focused_listitems(self):
        """Copy of the focused item. An empty container leaves the focused list empty."""
        return self.get_focused_listitems()

    def get_focused_listitems(self):
        if not self.container.numallitems:
            return ()
        return (self.focused_item.get_listitem(),)

    @cached_property
    def focused_previews(self):
        return self.get_focused_previews()

    def get_focused_previews(self):
        if not self.focused_list:
            return {}
        return {FOCUSED_LIST_ID: self.focused_listitems}

    @cached_property
    def previews(self):
        return self.get_previews()

    def get_previews(self):
        return {**self.view_previews, **self.focused_previews}
