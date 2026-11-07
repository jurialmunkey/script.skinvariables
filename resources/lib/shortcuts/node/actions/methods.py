# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.shortcuts.node.actions.navigation import NavigationMethods
from resources.lib.shortcuts.node.actions.editing import EditingMethods
from resources.lib.shortcuts.node.actions.lists import ListsMethods
from resources.lib.shortcuts.node.actions.movement import MovementMethods


class NodeMethods(NavigationMethods, EditingMethods, ListsMethods, MovementMethods):
    pass
