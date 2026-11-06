# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import ListItem
from jurialmunkey.litems import ContainerDirectory
from jurialmunkey.parser import boolean
from jurialmunkey.window import set_to_windowprop
from resources.lib.filterdir.editor import FilterDirEditor
from resources.lib.filterdir.items import FilterDirItems
from resources.lib.filterdir.labels import ContainerLabelItems
from resources.lib.filterdir.paths import FilterDirPaths, FallbackFilterDirPaths, RandomFilterDirPaths
from resources.lib.kodiutils import get_localized


class ListGetFilterFiles(ContainerDirectory):
    basepath = 'plugin://script.skinvariables/'
    folderpath = 'special://profile/addon_data/script.skinvariables/nodes/dynamic/'

    def get_file_item(self, filename):
        editpath = f'{self.basepath}?info=set_filter_dir&filepath={self.folderpath}{filename}'
        itempath = f'{self.basepath}?info=get_params_file&path={self.folderpath}{filename}'
        listitem = ListItem(label=filename, path=itempath)
        listitem.addContextMenuItems([(get_localized(32094), f'RunPlugin({editpath})')])
        return (itempath, listitem, True)

    def get_new_item(self):
        path = f'{self.basepath}?info=set_filter_dir'
        return (path, ListItem(label=f'{get_localized(32095)}...', path=path), True)

    def get_directory(self, filepath=None, **kwargs):
        from resources.lib.shortcuts.futils import get_files_in_folder
        files = get_files_in_folder(filepath or self.folderpath, r'.*\.json')
        items = [self.get_file_item(filename) for filename in files if filename]
        items.append(self.get_new_item())
        self.add_items(items)


class ListSetFilterDir(ContainerDirectory):
    def get_directory(self, library='video', filename=None, filepath=None, **kwargs):
        editor = FilterDirEditor(library=library, filepath=filepath)
        if filepath:
            return editor.edit()
        editor.create(filename)
        ListGetFilterFiles(self.handle, '').get_directory()


class ListGetFilterDir(ContainerDirectory):
    def get_directory(
        self,
        paths=None,
        library=None,
        no_label_dupes=False,
        dbtype=None,
        sort_by=None,
        sort_how=None,
        randomise=False,
        randomise_prop=None,
        randomise_time=None,
        fallback=False,
        names=None,
        infolabel=None,
        infoproperty=None,
        window_prop=None,
        window_id=None,
        **kwargs,
    ):
        if not paths:
            return
        source = self.get_paths(paths, names, randomise, fallback, randomise_prop, randomise_time)
        items = FilterDirItems(
            source,
            library=library,
            dbtype=dbtype,
            no_label_dupes=no_label_dupes,
            sort_by=sort_by,
            sort_how=sort_how,
            **kwargs,
        )
        self.add_items(items.directory_items, container_content=items.container_content)
        window_prop = window_prop or 'Statistics'
        self.set_properties(items.statistics, window_prop, window_id)
        self.set_item_properties(items.items, infolabel, 'infolabels', window_prop, window_id)
        self.set_item_properties(items.items, infoproperty, 'infoproperties', window_prop, window_id)

    @staticmethod
    def get_paths(paths, names, randomise, fallback, randomise_prop, randomise_time):
        if boolean(randomise):
            return RandomFilterDirPaths(paths, names, randomise_prop, randomise_time)
        if boolean(fallback):
            return FallbackFilterDirPaths(paths, names)
        return FilterDirPaths(paths, names)

    @staticmethod
    def set_properties(properties, window_prop, window_id):
        for key, value in properties.items():
            set_to_windowprop(value, key, window_prop, window_id)

    def set_item_properties(self, items, labels, attribute, window_prop, window_id):
        if not items or not labels:
            return
        self.clear_item_properties(labels, window_prop, window_id)
        properties = {
            f'{index}.{label}': getattr(item, attribute).get(label)
            for label in labels.split()
            for index, item in enumerate(items[:10])
        }
        self.set_properties(properties, window_prop, window_id)

    @staticmethod
    def clear_item_properties(labels, window_prop, window_id):
        import xbmc
        window_id_affix = f',{window_id}' if window_id else ''
        properties = (f'{window_prop}.{index}.{label}' for index in range(10) for label in labels.split())
        for key in properties:
            xbmc.executebuiltin(f'ClearProperty({key}{window_id_affix})')


class ListGetContainerLabels(ContainerDirectory):
    def get_directory(
        self,
        containers,
        infolabel,
        numitems=None,
        thumb=None,
        label2=None,
        separator=' / ',
        filter_value=None,
        filter_operator=None,
        exclude_value=None,
        exclude_operator=None,
        window_prop=None,
        window_id=None,
        contextmenu=None,
        **kwargs,
    ):
        items = ContainerLabelItems(
            containers,
            infolabel,
            thumb=thumb,
            label2=label2,
            separator=separator,
            contextmenu=contextmenu,
            filter_value=filter_value,
            filter_operator=filter_operator,
            exclude_value=exclude_value,
            exclude_operator=exclude_operator,
        )
        self.add_items(items.items)
        if not window_prop or not items.labels:
            return
        self.set_properties(items.labels, window_prop, window_id)

    @staticmethod
    def set_properties(labels, window_prop, window_id):
        import xbmc
        for index, item in enumerate(labels):
            set_to_windowprop(item, index, window_prop, window_id)
        titles = ' / '.join(item[0] for item in labels)
        window_id_affix = f',{window_id}' if window_id else ''
        xbmc.executebuiltin(f'SetProperty({window_prop},{titles}{window_id_affix})')
