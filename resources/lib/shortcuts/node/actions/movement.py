# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.shortcuts.node.actions.move import NodeMove, BoundaryNodeMove


class MovementMethods:
    def do_move(self, move=0, refocus=None, window_prop=None, window_id=None, offset=None, boundary=None):
        if boundary is None:
            movement = NodeMove(self.menunode, self.item, move, offset)
        else:
            movement = BoundaryNodeMove(self.menunode, self.item, boundary, move, offset)
        movement.apply()
        self.write_meta_to_file()
        index = self.menunode.index(movement.item)
        self.do_windowprop(window_prop, index, window_id)
        self.do_refocus(refocus, index)
