# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.litems import ContainerDirectory
from resources.lib.methods.builtins import run_executebuiltin


class ListRunExecuteBuiltin(ContainerDirectory):
    def get_directory(self, paths, **kwargs):
        for path in paths:
            run_executebuiltin(path, use_rules=True, **kwargs)
        self.add_items([self.get_list_item('None')])
