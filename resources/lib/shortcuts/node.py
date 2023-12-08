# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import random
import resources.lib.shortcuts.futils as shortcutfutils
from xbmcgui import ListItem, Dialog, INPUT_NUMERIC
from jurialmunkey.litems import Container
from jurialmunkey.parser import boolean, parse_localize
# from resources.lib.kodiutils import kodi_log
# from jurialmunkey.logger import TimerFunc

FILE_PREFIX = shortcutfutils.FILE_PREFIX

ICON_DIR = 'special://skin/extras/icons/'
SKIN_DIR = 'special://skin/shortcuts/'
CONTEXTMENU_CONFIGFILE = f'{SKIN_DIR}/skinvariables-shortcut-context.json'
ICON_FOLDER = f'{ICON_DIR}folder.png'
ICON_ADD = f'{ICON_DIR}circle-plus.png'
ICON_WIDGET = f'{ICON_DIR}shapes.png'
GROUPING_DEFAULT = 'grouping://shortcuts/'

WARNING_TEXT = '[B][COLOR=red]WARNING[/COLOR][/B]: This action cannot be undone.'
ACTION_HEADING = 'Action'
ICON_HEADING = 'Icon'
EDIT_HEADING = 'Edit'
DELETE_HEADING = 'Delete'
DELETE_MESSAGE = f'Are you sure you want to delete this item?\n{WARNING_TEXT}'
ADDITEM_LABEL = 'Add item...'
SUBMENU_HEADING = 'Submenu'
REBUILD_HEADING = 'Rebuild shortcuts'
REBUILD_MESSAGE = 'Rebuild shortcuts template to include recent changes?'
RESTORE_HEADING = 'Restore shortcuts'
RESTORE_MESSAGE = f'Restore shortcuts from skin defaults?\n{WARNING_TEXT}'
ADDLIST_HEADING = 'Add list of items'
ADDLIST_MESSAGE = '[B][COLOR=red]WARNING[/COLOR][/B]: Adding this list will add {item_count} new items (skipping {skip_count} existing items previously added). This action cannot be undone. Are you sure you want to continue?'
ADDLIST_NOITEMS_MESSAGE = 'No new items to add!'
ADDLIST_TOOMANY_MESSAGE = 'This list contains {item_count} items. The current max item limit is {item_limit}. This list will not be added.'
DELLIST_HEADING = 'Delete list of items'
DELLIST_MESSAGE = '[B][COLOR=red]WARNING[/COLOR][/B]: Deleting this list will remove {item_count} existing items. This action cannot be undone. Are you sure you want to continue?'
DELLIST_NOITEMS_MESSAGE = 'No items to delete!'


CONTEXTMENU_BASIC = [
    ["Choose shortcut", "do_choose", []],
    ["Action", "do_action", []],
    ["Rename", "do_edit", ["label"]],
    ["Icon", "do_icon", []],
    ["Move up", "do_move", ["-1"]],
    ["Move down", "do_move", ["1"]],
    ["Copy", "do_copy", []],
    ["Delete", "do_delete", []],
    ["Refresh shortcuts", "do_refresh", []],
    # ["Disable {disabled}", "do_toggle", []],
]


CONTEXTMENU_MAINMENU = [
    # ["Rebuild shortcuts", "do_rebuild", []],
    ["Restore shortcuts", "do_refresh", ["True"]],
    ["Configure submenu", "do_submenu", []],
    ["Configure widgets", "do_widgets", []],
]


def get_default_item():
    return {
        'label': '',
        'icon': '',
        'path': '',
        'target': '',
        'submenu': [],
        'widgets': []
    }


class FormatDict(dict):
    def __missing__(self, key):
        if 'listitem_obj' in self.keys():
            return self['listitem_obj'].getProperty(key)
        return ''


class ContextMenuDict(dict):
    def __getitem__(self, key):
        if key != 'basic':  # Basic menu should be appended to all other types
            return dict.__getitem__(self, 'basic') + dict.__getitem__(self, key)
        return dict.__getitem__(self, key)

    def __missing__(self, key):
        if key == 'basic':
            return CONTEXTMENU_BASIC
        if key == 'mainmenu':
            return CONTEXTMENU_MAINMENU
        return []


def get_contextmenu_config():
    return ContextMenuDict(shortcutfutils.read_meta_from_file(CONTEXTMENU_CONFIGFILE) or {})


def get_contextmenu(node, mode='submenu'):
    contextmenu = get_contextmenu_config()
    if not node:
        return contextmenu['mainmenu']
    if mode == 'widgets':
        return contextmenu['widgets']
    return contextmenu['basic']


def get_submenunode(meta, mode='submenu'):
    try:
        return meta[mode]
    except KeyError:
        meta[mode] = []
        return meta[mode]


def get_submenuitem(meta, n):
    try:
        return meta[n]
    except IndexError:
        meta.append(get_default_item())
        return meta[-1]


def get_menuguid(meta, guid, mode='submenu', subkeys=('submenu', 'widgets')):
    """ Lookup menu node using guid and return tuple of meta for item and current node """
    if not meta or not guid:
        return

    def get_menuguid_item(item, node):
        name = parse_localize(item.get('label', ''))
        if item.get('guid') == guid:
            return (get_submenunode(item, mode), node, name)
        for k in subkeys:
            subitem, subnode, subname = get_menuguid_iter(item.get(k) or [])
            if not isinstance(subitem, list):
                continue
            subnode = subnode + node
            return (subitem, subnode, subname)
        return (None, None, None)

    def get_menuguid_iter(menu):
        for x, i in enumerate(menu):
            item, node, name = get_menuguid_item(i, [x])
            if not isinstance(item, list):
                continue
            return (item, node, name)
        return (None, None, None)

    item, node, name = get_menuguid_iter(meta)
    return (item, tuple(node), name) if node else (item, tuple(), name)


def get_menunode(meta, node, mode='submenu'):
    """ Lookup menu node using node value and return tuple of meta for item and current node """
    if not meta or not node:  # Return base of meta if no node because were in main menu
        return (meta, node, '')

    for n in node[:-1]:  # Walk submenus until last item
        meta = get_submenuitem(meta, n)
        meta = get_submenunode(meta)

    for n in node[-1:]:  # Last item we get in the current mode
        meta = get_submenuitem(meta, n)
        name = parse_localize(meta.get('label', ''))
        meta = get_submenunode(meta, mode)

    return (meta, node, name)


def get_nodename(node):
    return '.'.join([f'{n}' for n in node])


def get_menunode_item(menunode, x):
    try:
        return menunode[x]
    except IndexError:
        menunode.append(get_default_item())
        return menunode[x]


def assign_guid(meta):
    id_list = []

    def get_unique_guid(guid=None):
        guid = guid or f'guid-{random.randrange(16**8):08x}'
        return guid if guid not in id_list else get_unique_guid()

    def set_unique_guid(item):
        item['guid'] = get_unique_guid(item.get('guid'))
        return item['guid']

    def walk_item_lists(meta):
        for item in meta:
            id_list.append(set_unique_guid(item))
            walk_item_lists(item['submenu']) if 'submenu' in item else None
            walk_item_lists(item['widgets']) if 'widgets' in item else None

    walk_item_lists(meta) if meta else None
    return meta


def cache_meta_from_file(filepath, fileprop, refresh=False):
    meta = shortcutfutils.read_meta_from_prop(fileprop) if not refresh else None
    if meta is None:
        meta = shortcutfutils.read_meta_from_file(filepath)
        meta = assign_guid(meta)
        shortcutfutils.write_meta_to_prop(meta, fileprop)
    return meta


class GetDirectoryItems():
    def __init__(self, grouping=GROUPING_DEFAULT, use_rawpath=False, folder_name=None):
        self.grouping = grouping
        self.use_rawpath = use_rawpath
        self.folder_name = folder_name

    @property
    def directory_browser(self):
        try:
            return self._directory_browser
        except AttributeError:
            from resources.lib.shortcuts.browser import GetDirectoryBrowser
            self._directory_browser = GetDirectoryBrowser(use_rawpath=True, allow_links=False, folder_name=self.folder_name)
            return self._directory_browser

    @property
    def directory_jsonrpc(self):
        try:
            return self._directory_jsonrpc
        except AttributeError:
            from resources.lib.shortcuts.jsonrpc import GetDirectoryJSONRPC
            self._directory_jsonrpc = GetDirectoryJSONRPC(self.item_folder['path'], definitions=self.directory_browser.definitions, target=self.item_folder['target'])
            return self._directory_jsonrpc

    @property
    def item_folder(self):
        try:
            return self._item_folder
        except AttributeError:
            self._item_folder = self.get_item_folder()
            return self._item_folder

    @property
    def items(self):
        try:
            return self._items
        except AttributeError:
            self._items = self.get_items()
            return self._items

    def get_item_folder(self):
        from jurialmunkey.window import WindowProperty
        with WindowProperty(('IsSkinShortcut', 'True')):
            self._item_folder = self.directory_browser.get_directory(path=self.grouping)
        return self._item_folder

    def get_items(self):
        if not self.item_folder:
            return

        if not self.directory_jsonrpc.items:
            return

        if not boolean(self.use_rawpath):
            self.directory_browser.use_rawpath = False
            self.directory_browser.allow_links = True

        def _configure_item(i):
            i[1].setProperty('isfolder', 'True' if i[2] else 'False')
            return i

        return (self.directory_browser.get_new_item(_configure_item(i), allow_browsing=False) for i in self.directory_jsonrpc.items)


class NodeProperties():
    @property
    def fileprop(self):
        try:
            return self._fileprop
        except AttributeError:
            if not self.skin or not self.filename:
                return
            self._fileprop = f'{self.skin}-{self.filename}'
            return self._fileprop

    @property
    def filepath(self):
        try:
            return self._filepath
        except AttributeError:
            if not self.skin or not self.filename:
                return
            self._filepath = f'{shortcutfutils.ADDON_DATA}{self.skin}/{self.filename}'
            return self._filepath

    @property
    def filename(self):
        try:
            return self._filename
        except AttributeError:
            if not self.menu:
                return
            self._filename = shortcutfutils.validify_filename(f'{FILE_PREFIX}{self.menu}.json')
            return self._filename

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
            self._menunode, self.node, self.name = get_menuguid(self.meta, self.guid, self.mode) or get_menunode(self.meta, self.node, self.mode)
            return self._menunode

    @property
    def nodename(self):
        try:
            return self._nodename
        except AttributeError:
            self._nodename = get_nodename(self.node)
            return self._nodename


class NodeSubmenuMethods():
    def do_submenu_item(self, mode='submenu'):
        x = int(self.item)
        from resources.lib.shortcuts.browser import GetDirectoryBrowser
        from jurialmunkey.window import WindowProperty
        with WindowProperty(('IsSkinShortcut', 'True')):
            item = GetDirectoryBrowser().get_directory()
        if not item:
            return
        self.get_menunode_item(x).setdefault(mode, []).append(item)
        self.write_meta_to_file()

    def do_widgets_item(self):
        self.do_submenu_item('widgets')

    def do_submenu(self, mode='submenu'):

        node = [str(i) for i in self.node] + [str(self.item)]
        node = '.'.join(node)

        def get_choices_item(i):
            item = i[1]
            item.setLabel2(i[0])
            icon = item.getArt('icon') or item.getArt('thumb') or ICON_WIDGET
            item.setArt({'icon': icon, 'thumb': icon})
            return item

        def get_add_item():
            item = ListItem(label=ADDITEM_LABEL)
            item.setArt({'icon': ICON_ADD, 'thumb': ICON_ADD})
            return item

        # Generate new class object for node and get items to select
        submenu_container = ListGetShortcutsNode(self.handle, self.paramstring, **self.params)
        items = submenu_container.get_directory(menu=self.menu, skin=self.skin, node=node, mode=mode, func='list')
        choices = [get_choices_item(i) for i in items] + [get_add_item()]
        x = Dialog().select(SUBMENU_HEADING, list=choices, useDetails=True)

        # User cancelled so we leave
        if x == -1:
            return

        contextmenu = get_contextmenu(node, mode)

        y = 0  # TODO CHECK FOR CUSTOM LIST CONTEXT
        if x != len(items):  # Last item is ADD so we dont show contextmenu for it. We always do choose shortcut for ADD.
            item = choices[x]
            format_mapping = {'label': item.getLabel(), 'listitem_obj': item}
            format_mapping = FormatDict(format_mapping)
            y = Dialog().select(item.getLabel(), list=[cm_label.format_map(format_mapping) for cm_label, *_ in contextmenu])

        # User cancelled so we go back to original dialog
        if y == -1:
            return self.do_submenu(mode)

        # Generate new class object for item and do the action
        from copy import deepcopy
        action = contextmenu[y][1]
        params = deepcopy(self.params)
        params['paths'] = contextmenu[y][2]
        submenu_container = ListGetShortcutsNode(-1, '', **params)
        submenu_container.get_directory(menu=self.menu, skin=self.skin, node=node, mode=mode, item=x, func=action)

        return self.do_submenu(mode)

    def do_widgets(self):
        return self.do_submenu(mode='widgets')


class NodeMethods():
    def get_menunode_item(self, x):
        return get_menunode_item(self.menunode, x)

    def do_refresh(self, restore=False, executebuiltin=None):
        restore = boolean(restore)
        if restore and not Dialog().yesno(RESTORE_HEADING, RESTORE_MESSAGE):
            return
        self._meta = self.get_meta(refresh=True, restore=restore)
        self.do_rebuild(dialog=False, executebuiltin=executebuiltin)

    def do_rebuild(self, dialog=True, executebuiltin=None):
        if dialog and not Dialog().yesno(REBUILD_HEADING, REBUILD_MESSAGE):
            return
        self.write_meta_to_file(reload=False)
        from resources.lib.script import Script
        Script(paramstring=f'action=buildtemplate&force').run()
        if not executebuiltin:
            return
        import xbmc
        xbmc.Monitor().waitForAbort(0.4)
        xbmc.executebuiltin(executebuiltin)

    def do_open(self):
        x = int(self.item)
        path = self.get_menunode_item(x).get('path')
        target = self.get_menunode_item(x).get('target')
        if not path:
            return
        import xbmc
        import xbmcplugin
        xbmcplugin.setResolvedUrl(self.handle, False, ListItem())
        xbmc.Monitor().waitForAbort(0.2)
        xbmc.executebuiltin('ActivateWindow({target},{path},return)' if target else path)

    def do_icon(self, key='icon', value=None, heading=ICON_HEADING, icon_dir=ICON_DIR):
        """
        Set property[key] to value or prompt user to browse images in icon_dir if no value specified
        """
        x = int(self.item)
        new_value = value or Dialog().browse(type=2, heading=heading, useThumbs=True, defaultt=icon_dir, shares="")
        if not new_value or new_value == -1 or new_value == icon_dir:
            return
        self.get_menunode_item(x)[key] = new_value
        self.write_meta_to_file()

    def do_copy(self):
        x = int(self.item)
        from copy import deepcopy
        self.menunode.append(deepcopy(self.get_menunode_item(x)))
        self.write_meta_to_file()

    def do_delete(self, warning=True):
        x = int(self.item)
        n = Dialog().yesno(heading=DELETE_HEADING, message=DELETE_MESSAGE) if boolean(warning) else 1
        if not n or n == -1:
            return
        self.menunode.pop(x)
        self.write_meta_to_file()

    def do_toggle(self, key='disabled'):
        """
        Toggles property[key] between 'True' and empty
        """
        x = int(self.item)
        current = self.get_menunode_item(x).get(key)
        self.get_menunode_item(x)[key] = 'True' if not current else ''
        self.write_meta_to_file()

    def do_executebuiltin(self, *args):
        if not args:
            return
        import xbmc
        for i in args:
            xbmc.executebuiltin(i)

    def do_edit(self, key='label', value=None, heading=EDIT_HEADING, use_prop_pairs=False):
        """
        key, value = property to edit and value to set
        heading = heading of select dialog when use_prop_pairs enabled
        use_prop_pairs allows for selecting key/values using & separated list with = partition for key value pairs
            -- e.g. foo=bar&fizz=buzz will show a list with foo|fizz as options that set bar|buzz respectively
            -- 'edit' as value will prompt input via keyboard
            -- 'null' as value will delete value for key
        """
        x = int(self.item)

        def _get_items():
            items = [(k, v if s else k) for k, s, v in (i.partition('=') for i in value.split("&") if i)]
            choice = Dialog().select(heading=heading, list=[i[0] for i in items])
            if choice == -1:
                return -1
            choice = items[choice][1]
            if choice == 'edit':
                return None
            return choice

        def _get_input():
            return Dialog().input(heading=heading, defaultt=parse_localize(self.get_menunode_item(x).get(key) or ''))

        if boolean(use_prop_pairs):
            value = _get_items()
        if value is None:
            value = _get_input()
        if value == -1:
            return
        if not value:
            return

        self.get_menunode_item(x)[key] = value if value != 'null' else ''
        self.write_meta_to_file()

    def do_numeric(self, key='limit', value=None, heading=EDIT_HEADING):
        """
        Set property[key] to a numeric value.
        Prompts for user input if value not specified.
        """
        x = int(self.item)

        if not value and value != 0:
            value = Dialog().input(heading=heading, type=INPUT_NUMERIC, defaultt=parse_localize(self.get_menunode_item(x).get(key) or ''))
        if value == -1:
            return

        self.get_menunode_item(x)[key] = str(value or '')
        self.write_meta_to_file()

    def do_action(self, prefix=None, grouping=GROUPING_DEFAULT, use_rawpath=False):
        """
        Update path and target for item by giving user option to browse or edit
        Specify prefix to set a specific property e.g. prefix=myshortcut updates myshortcut_path myshortcut_target
        Specify grouping to open at grouping other than basedir default
        """
        x = int(self.item)
        menunode_item = self.get_menunode_item(x)
        path = menunode_item.get('path') or ''
        target = menunode_item.get('target') or ''
        a = Dialog().yesnocustom(
            heading=ACTION_HEADING, message=path,
            yeslabel='Edit', nolabel='Browse', customlabel='Cancel')
        if a == 2 or a == -1:
            return
        if a == 1:
            path = Dialog().input(heading=ACTION_HEADING, defaultt=path)
        else:
            from resources.lib.shortcuts.browser import GetDirectoryBrowser
            from jurialmunkey.window import WindowProperty
            with WindowProperty(('IsSkinShortcut', 'True')):
                item = GetDirectoryBrowser(use_rawpath=boolean(use_rawpath)).get_directory(path=grouping)
            try:
                path = item['path']
                target = item['target']
            except TypeError:
                return
        if not path:
            return
        prefix = f'{prefix}_' if prefix else ''
        item = {
            f'{prefix}path': path,
            f'{prefix}target': target
        }
        menunode_item.update(item)
        self.write_meta_to_file()

    def do_list_del(self, grouping=GROUPING_DEFAULT, use_rawpath=False):
        directory_item_getter = GetDirectoryItems(grouping=grouping, use_rawpath=use_rawpath, folder_name='Delete list...')
        items = directory_item_getter.items or []
        paths = [i['path'] for i in items if i and i.get('path')]
        index = [x for x, i in enumerate(self.menunode) if i and i.get('path') in paths]
        if not index:
            Dialog().ok(DELLIST_HEADING, DELLIST_NOITEMS_MESSAGE)
            return
        if not Dialog().yesno(DELLIST_HEADING, DELLIST_MESSAGE.format(item_count=len(index))):
            return
        for x in sorted(index, reverse=True):
            del self.menunode[x]
        self.write_meta_to_file()

    def do_list_add(self, grouping=GROUPING_DEFAULT, use_rawpath=False, item_limit=30):
        """
        Choose a list to add multiple items automatically
        """
        x = int(self.item)
        item_limit = int(item_limit)

        directory_item_getter = GetDirectoryItems(grouping=grouping, use_rawpath=use_rawpath, folder_name='Add list...')
        items = directory_item_getter.items
        if not items:
            Dialog().ok(ADDLIST_HEADING, ADDLIST_NOITEMS_MESSAGE)
            return
        directory_jsonrpc_items = directory_item_getter.directory_jsonrpc.items

        paths = [i['path'] for i in self.menunode if i and i.get('path')]
        items = [i for i in items if i and i['path'] not in paths]

        if len(items) < 1:
            Dialog().ok(ADDLIST_HEADING, ADDLIST_NOITEMS_MESSAGE)
            return

        if len(items) > item_limit:
            Dialog().ok(ADDLIST_HEADING, ADDLIST_TOOMANY_MESSAGE.format(item_count=len(items), item_limit=item_limit))
            return

        if not Dialog().yesno(ADDLIST_HEADING, ADDLIST_MESSAGE.format(
                item_count=len(items),
                skip_count=len(directory_jsonrpc_items) - len(items))):
            return

        for y, item in enumerate(items):
            self.menunode.insert(x + y + 1, item)  # Add enumerator to original position to insert in order

        self.write_meta_to_file()

    def do_choose(self, prefix=None, grouping=GROUPING_DEFAULT, create_new=False, use_rawpath=False):
        """
        Wrapper for do_action which also sets icon and label
        Specify prefix to set a specific property e.g. prefix=myshortcut updates myshortcut_path myshortcut_target myshortcut_icon myshortcut_label
        Specify create_new boolean to insert in place, otherwise updates item
        """
        x = int(self.item)
        from resources.lib.shortcuts.browser import GetDirectoryBrowser
        from jurialmunkey.window import WindowProperty
        with WindowProperty(('IsSkinShortcut', 'True')):
            item = GetDirectoryBrowser(use_rawpath=boolean(use_rawpath)).get_directory(path=grouping)
        if not item:
            return
        item = {f'{prefix}_{k}': v for k, v in item.items()} if prefix else item
        self.menunode.insert(x + 1, item) if boolean(create_new) else self.get_menunode_item(x).update(item)
        self.write_meta_to_file()

    def do_new(self, prefix=None, grouping=GROUPING_DEFAULT, use_rawpath=False):
        """
        Wrapper for do_choose that forces create_new=True
        """
        self.do_choose(prefix=prefix, grouping=grouping, create_new=True, use_rawpath=use_rawpath)

    def do_move(self, move=0, refocus=None):
        x = int(self.item)
        self.menunode.insert(x + int(move), self.menunode.pop(x))
        self.write_meta_to_file()
        if not refocus:
            return
        import xbmc
        xbmc.Monitor().waitForAbort(0.2)  # Wait a moment before refocusing to make sure we
        xbmc.executebuiltin(f'SetFocus({refocus},{x + int(move)},absolute)')


class ListGetShortcutsNode(Container, NodeProperties, NodeMethods, NodeSubmenuMethods):
    refresh = False
    update_listing = False

    def get_meta(self, refresh=False, restore=False):
        if not self.filepath:
            return
        meta = cache_meta_from_file(self.filepath, fileprop=self.fileprop, refresh=refresh) if not restore else None
        if meta is None:
            meta = cache_meta_from_file(f'{SKIN_DIR}{self.filename}', fileprop=self.fileprop, refresh=refresh)  # Get from skin
            shortcutfutils.write_meta_to_file(meta, folder=self.skin, filename=self.filename, fileprop=self.fileprop) if meta is not None else None  # Write to addon_data
        return meta

    def write_meta_to_file(self, reload=True):
        shortcutfutils.write_meta_to_file(assign_guid(self.meta), folder=self.skin, filename=self.filename, fileprop=self.fileprop, reload=reload)

    def get_directory_items(self, blank=False):

        contextmenu = get_contextmenu_config()

        def _make_item(x, i):
            if (not i or boolean(i.get('disabled'))) and not blank and not self.edit:
                return

            url = f'plugin://script.skinvariables/?info=get_shortcuts_node&menu={self.menu}&skin={self.skin}&mode={self.mode}&item={x}'
            url = url if not self.node else f'{url}&node={node_name}'
            url = url if not self.guid else f'{url}&guid={self.guid}'
            list_name = f'{node_name}.{x}' if self.node else f'{x}'

            i['item'] = f'{x}'
            i['node'] = f'{node_name}' if self.node else ''
            i['list'] = f'{list_name}' if list_name else ''
            i['menu'] = f'{self.menu}' if self.menu else ''
            i['skin'] = f'{self.skin}' if self.skin else ''
            i['mode'] = f'{self.mode}' if self.mode else ''
            i['name'] = f'{self.name}' if self.name else ''

            submenu = i.pop('submenu', [])
            widgets = i.pop('widgets', [])

            target = i.get('target', '')
            name = parse_localize(i.pop('label', ''))
            path = i.get('path', '')  # if target else f'{url}&func=do_open'
            icon = i.pop('icon', '')

            listitem = ListItem(label=name, label2='', path=path, offscreen=True)
            listitem.setArt({'icon': icon, 'thumb': icon})
            listitem.setProperties({k: v for k, v in i.items() if k and v})
            listitem.setProperty('isPlayable', 'True') if not target else None
            listitem.setProperty('target', target)
            listitem.setProperty('url', url)
            listitem.setProperty('label', name)
            listitem.setProperty('hasSubmenu', 'True') if submenu else None
            listitem.setProperty('hasWidgets', 'True') if widgets else None
            listitem_isfolder = True if target else False

            contextitems = contextmenu['basic']
            if not self.node:  # Main menu options
                contextitems = contextmenu['mainmenu']
            format_mapping = {'label': name, 'path': path, 'icon': icon, 'name': name, 'target': target}
            format_mapping.update(i)
            format_mapping = FormatDict(format_mapping)
            listitem_contextmenu = [
                (cm_label.format_map(format_mapping), f'RunPlugin({url}&func={cm_action}{"&&" if cm_params else ""}{"&&".join(cm_params)})'.format_map(format_mapping), )
                for cm_label, cm_action, cm_params in contextitems]

            listitem.addContextMenuItems(listitem_contextmenu)
            item = (path, listitem, listitem_isfolder, )
            return item

        node_name = get_nodename(self.node)
        items = [_make_item(0, {})] if blank else [j for j in (_make_item(x, i) for x, i in enumerate(self.menunode or [])) if j]
        return items

    def get_directory(
            self,
            menu=None,  # The menu filename
            skin=None,  # The skin addon ID
            item=None,  # The item index of the current menu
            node=None,  # Tuple of point separated submenu indicies to get to current level
            mode=None,  # Get widgets or submenu items - defaults to submenu
            func=None,  # The method to run
            guid=None,  # Unique identifier for group
            edit=None,  # Edit mode if on all items are shown even if disabled
            **kwargs
    ):

        self.menu = menu
        self.skin = skin
        self.mode = mode or 'submenu'
        self.guid = guid
        self.edit = boolean(edit)

        try:
            self.node = tuple([int(i) for i in node.split('.') if i])
        except (TypeError, AttributeError):
            self.node = tuple()

        try:
            self.item = item
        except TypeError:
            self.item = None

        if func == 'node':
            return self.menunode

        if (self.item is None or not self.meta) and func in [None, 'list']:  # If no item is specified then we show the whole directory
            items = self.get_directory_items(blank=True if not self.menunode and self.edit else False)  # If we're in edit mode and have no items show a blank one
            return items if func == 'list' else self.add_items(items, update_listing=self.update_listing)

        item_func = getattr(self, func)

        if not self.meta and self.filepath:
            self._meta = [get_default_item()]  # Create a blank item in meta to write to if we're trying to do a function on it.

        path_partitions = [i.partition('::') if i else ('', '', '', ) for i in self.params.get('paths', [])]
        path_args = [k for k, s, v in path_partitions if not s]
        path_kwargs = {k: v for k, s, v in path_partitions if s}
        item_func(*path_args, **path_kwargs)  # If an item is specified we do its function
