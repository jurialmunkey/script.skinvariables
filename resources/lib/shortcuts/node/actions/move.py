# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from jurialmunkey.parser import boolean


class NodeMove:
    def __init__(self, items, index, move=0, offset=None):
        self.items = items
        self.index = int(index)
        self.move = int(move)
        self.offset = offset
        self.item = self.items.pop(self.index)
        self.size = len(self.items)

    @cached_property
    def destination(self):
        return self.get_destination()

    def get_destination(self):
        if self.offset is None:
            return self.index + self.move
        if self.move < 0:
            return int(self.offset) + 1 + self.move
        if self.move > 0:
            return int(self.offset) - 1 + self.move
        return int(self.offset)

    def apply(self):
        destination = self.destination if self.destination <= self.size else 0
        destination = destination if destination >= 0 else self.size + 1
        self.items.insert(destination, self.item)
        return self.items.index(self.item)


class BoundaryNodeMove(NodeMove):
    def __init__(self, items, index, boundary, move=0, offset=None):
        self.boundary = int(boundary)
        super().__init__(items, index, move, offset)

    def is_disabled(self, index):
        return boolean(self.items[index].get('disabled'))

    @cached_property
    def crosses_lower(self):
        return self.get_crosses_lower()

    def get_crosses_lower(self):
        return self.move < 0 and self.index >= self.boundary and all(
            self.is_disabled(index)
            for index in range(self.boundary, self.index)
        )

    @cached_property
    def crosses_upper(self):
        return self.get_crosses_upper()

    def get_crosses_upper(self):
        return self.move > 0 and self.index < self.boundary and all(
            self.is_disabled(index)
            for index in range(self.index, self.boundary - 1)
        )

    def move_lower(self):
        swap = next((index for index in range(self.boundary - 1, -1, -1) if self.is_disabled(index)), self.boundary - 1)
        self.items.insert(self.boundary - 1, self.items.pop(swap))
        return self.boundary - 1

    def move_upper(self):
        if self.boundary - 1 >= self.size:
            return self.size
        swap = next(
            (index for index in range(self.boundary - 1, self.size) if self.is_disabled(index)),
            self.boundary - 1,
        )
        self.items.insert(self.boundary - 1, self.items.pop(swap))
        return self.boundary

    def get_destination(self):
        destination = super().get_destination()
        if self.crosses_lower:
            return self.move_lower()
        if self.crosses_upper:
            return self.move_upper()
        return destination
