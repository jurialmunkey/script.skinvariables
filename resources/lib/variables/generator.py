# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from itertools import product
from jurialmunkey.ftools import cached_property
from resources.lib.variables.items import VariableItem, ExpressionItem, ParentVariableItem


class VariableDefinition:
    item_class = VariableItem

    def __init__(self, variable):
        self.variable = variable

    @cached_property
    def containers(self):
        return self.get_containers()

    def get_containers(self):
        return self.variable.get('containers', []) + ['']

    @cached_property
    def item_containers(self):
        return self.get_item_containers()

    def get_item_containers(self):
        if self.variable.get('null_id', '').lower() == 'true':
            return self.containers + [-1]
        return self.containers

    @cached_property
    def listitems(self):
        return self.get_listitems()

    def get_listitems(self):
        start = self.variable.get('listitems', {}).get('start', 0)
        end = self.variable.get('listitems', {}).get('end')
        return list(range(start, int(end) + 1)) + [''] if end else ['']

    @cached_property
    def listitem_types(self):
        return self.get_listitem_types()

    def get_listitem_types(self):
        return self.variable.get('types') or ['listitem']

    @cached_property
    def items(self):
        return self.get_items()

    def get_items(self):
        return [
            self.item_class(self.variable, container, listitem, listitem_type).result
            for listitem_type, container, listitem in product(
                self.listitem_types,
                self.item_containers,
                self.listitems,
            )
        ]

    @cached_property
    def parents(self):
        return self.get_parents()

    def get_parents(self):
        if not self.variable.get('parent'):
            return []
        return [
            ParentVariableItem(self.variable, self.containers, listitem_type).result
            for listitem_type in self.listitem_types
        ]

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        return self.items + self.parents


class ExpressionDefinition(VariableDefinition):
    item_class = ExpressionItem


class VariablesBuilder:
    def __init__(self, meta):
        self.meta = meta

    def get_definition(self, variable):
        if not variable.get('name'):
            return
        if variable.get('values'):
            return VariableDefinition(variable)
        if variable.get('expression'):
            return ExpressionDefinition(variable)

    @cached_property
    def definitions(self):
        return self.get_definitions()

    def get_definitions(self):
        definitions = (self.get_definition(variable) for variable in self.meta)
        return [definition for definition in definitions if definition is not None]

    @cached_property
    def xmltree(self):
        return self.get_xmltree()

    def get_xmltree(self):
        return [element for definition in self.definitions for element in definition.result]
