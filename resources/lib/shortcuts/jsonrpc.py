from resources.lib.shortcuts.common import GetDirectoryCommon


DIRECTORY_PROPERTIES_BASIC = ["title", "art", "file", "fanart"]


class GetDirectoryJSONRPC(GetDirectoryCommon):
    def get_directory(self):
        if not self.path:
            return []
        from jurialmunkey.jsnrpc import get_directory
        self._directory = get_directory(self.path, DIRECTORY_PROPERTIES_BASIC)
        # from resources.lib.shortcuts.futils import dumps_log_to_file
        # dumps_log_to_file(self._directory)
        return self._directory

    def get_items(self):

        from resources.lib.lists.filterdir import ListItemJSONRPC

        def _make_item(i):
            if not i:
                return
            listitem_jsonrpc = ListItemJSONRPC(i, library=self.library, dbtype=self.dbtype)
            listitem_jsonrpc.infolabels['title'] = listitem_jsonrpc.label
            listitem_jsonrpc.infoproperties['nodetype'] = self.target or ''
            listitem_jsonrpc.artwork = self.get_artwork_fallback(listitem_jsonrpc)
            listitem_jsonrpc.label2 = listitem_jsonrpc.path
            item = (listitem_jsonrpc.path, listitem_jsonrpc.listitem, listitem_jsonrpc.is_folder, )
            return item

        from resources.lib.kodiutils import ProgressDialog
        with ProgressDialog('Skin Variables', f'Building directory...\n{self.path}', total=1, logging=2, background=False):
            if not self.directory:
                return []
            return [j for j in (_make_item(i) for i in self.directory) if j]
