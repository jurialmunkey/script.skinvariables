# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.shortcuts.node.actions.properties import PropertyEdit
from xbmcgui import Dialog, INPUT_NUMERIC
from jurialmunkey.parser import boolean, parse_localize
from resources.lib.kodiutils import get_localized
from resources.lib.shortcuts.node.constants import ICON_DIR, GROUPING_DEFAULT


class EditingMethods:
    def do_icon(self, key='icon', value=None, heading=None, icon_dir=ICON_DIR):
        """
        Set property[key] to value or prompt user to browse images in icon_dir if no value specified
        """
        x = int(self.item)

        heading = heading or get_localized(32077)

        new_value = value or Dialog().browse(type=2, heading=heading, useThumbs=True, defaultt=icon_dir, shares="files")
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
        n = Dialog().yesno(heading=get_localized(117), message=get_localized(32043)) if boolean(warning) else 1
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

    def do_edit(self, key='label', value=None, heading=None, use_prop_pairs=False):
        item = self.get_menunode_item(int(self.item))
        editor = PropertyEdit(item, key, heading or get_localized(21435), value)
        if boolean(use_prop_pairs):
            value = editor.select()
        if value is None:
            value = editor.input()
        if value == -1 or not value:
            return
        item[key] = value if value != 'null' else ''
        self.write_meta_to_file()

    def do_numeric(self, key='limit', value=None, heading=None):
        """
        Set property[key] to a numeric value.
        Prompts for user input if value not specified.
        """
        x = int(self.item)

        heading = heading or get_localized(21435)

        if not value and value != 0:
            value = Dialog().input(
                heading=heading,
                type=INPUT_NUMERIC,
                defaultt=parse_localize(self.get_menunode_item(x).get(key) or ''),
            )
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
            heading=get_localized(15217),
            message=path,
            yeslabel='Edit',
            nolabel='Browse',
            customlabel='Cancel',
        )
        if a == 2 or a == -1:
            return
        if a == 1:
            path = Dialog().input(heading=get_localized(15217), defaultt=path)
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
        item = {f'{prefix}path': path, f'{prefix}target': target}
        menunode_item.update(item)
        self.write_meta_to_file()

    def do_choose(
        self,
        prefix=None,
        grouping=GROUPING_DEFAULT,
        create_new=False,
        use_rawpath=False,
        refocus=None,
        window_prop=None,
        window_id=None,
        **kwargs,
    ):
        """
        Wrapper for do_action which also sets icon and label
        Specify prefix to set the corresponding path, target, icon, and label properties.
        Specify create_new boolean to insert in place, otherwise updates item
        Specify additional kwargs to add default properties to item
        """
        x = int(self.item)
        from resources.lib.shortcuts.browser import GetDirectoryBrowser
        from jurialmunkey.window import WindowProperty
        with WindowProperty(('IsSkinShortcut', 'True')):
            item = GetDirectoryBrowser(use_rawpath=boolean(use_rawpath)).get_directory(path=grouping)
        if not item:
            return
        item.update(kwargs)  # Allow adding in additional forced properties
        item = {f'{prefix}_{k}': v for k, v in item.items()} if prefix else item
        if boolean(create_new):
            x = x + 1
            self.menunode.insert(x, item)
        else:
            self.get_menunode_item(x).update(item)
        self.write_meta_to_file()

        self.do_windowprop(window_prop, x, window_id)
        self.do_refocus(refocus, x)

    def do_new(
        self,
        prefix=None,
        grouping=GROUPING_DEFAULT,
        use_rawpath=False,
        refocus=None,
        window_prop=None,
        window_id=None,
        **kwargs,
    ):
        """
        Wrapper for do_choose that forces create_new=True
        """
        self.do_choose(
            prefix=prefix,
            grouping=grouping,
            create_new=True,
            use_rawpath=use_rawpath,
            refocus=refocus,
            window_prop=window_prop,
            window_id=window_id,
            **kwargs,
        )
