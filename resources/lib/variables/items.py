# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property


LISTITEM_TYPE_TAGS = {'listitem': '', 'listitemabsolute': '_LIA', 'listitemnowrap': '_LIN', 'listitemposition': '_LIP'}


class VariableElement:
    tag = 'variable'

    def __init__(self, variable, listitem_type='listitem'):
        self.variable = variable
        self.listitem_type = listitem_type

    @cached_property
    def name(self):
        return self.get_name()

    def get_name(self):
        return self.variable['name'] + LISTITEM_TYPE_TAGS[self.listitem_type]

    @cached_property
    def content(self):
        return self.get_content()

    def get_content(self):
        raise NotImplementedError

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        return {'tag': self.tag, 'attrib': {'name': self.name}, 'content': self.content}


class VariableItem(VariableElement):
    def __init__(self, variable, container, listitem, listitem_type='listitem'):
        super().__init__(variable, listitem_type)
        self.container = container
        self.listitem = listitem

    @cached_property
    def container_id(self):
        return self.get_container_id()

    def get_container_id(self):
        return '' if self.container == -1 else self.container or ''

    @cached_property
    def container_suffix(self):
        return self.get_container_suffix()

    def get_container_suffix(self):
        return f'_C{self.container_id}' if self.container_id else ''

    @cached_property
    def listitem_suffix(self):
        return self.get_listitem_suffix()

    def get_listitem_suffix(self):
        return f'_{self.listitem}' if self.listitem or self.listitem == 0 else ''

    def get_name(self):
        container_suffix = '_Container' if self.container == -1 else self.container_suffix
        return super().get_name() + container_suffix + self.listitem_suffix

    @cached_property
    def listitem_label(self):
        return self.get_listitem_label()

    def get_listitem_label(self):
        label = 'ListItem'
        if self.container == -1:
            label = 'Container.ListItem'
        elif self.container_id:
            label = f'Container({self.container_id}).ListItem'
        if self.listitem_suffix:
            label += f'({self.listitem})'
        return label

    @cached_property
    def format_values(self):
        return self.get_format_values()

    def get_format_values(self):
        values = {
            'id': self.container_id,
            'cid': self.container_suffix,
            'lid': self.listitem_suffix,
            'pos': self.listitem or 0,
            'listitem': self.listitem_label,
            'listitemabsolute': self.listitem_label.replace('ListItem(', 'ListItemAbsolute('),
            'listitemnowrap': self.listitem_label.replace('ListItem(', 'ListItemNoWrap('),
            'listitemposition': self.listitem_label.replace('ListItem(', 'ListItemPosition('),
        }
        values['listitem'] = values[self.listitem_type]
        return values

    def get_value(self, value):
        result = {'tag': 'value', 'attrib': {}}
        for condition, content in value.items():
            if not condition:
                continue
            result['attrib']['condition'] = condition.format(**self.format_values)
            result['content'] = content.format(**self.format_values) if content else ''
        return result

    def get_content(self):
        return [self.get_value(value) for value in self.variable.get('values', [])]


class ExpressionItem(VariableItem):
    tag = 'expression'

    def get_content(self):
        return self.variable.get('expression', '').format(**self.format_values)


class ParentVariableItem(VariableElement):
    def __init__(self, variable, containers, listitem_type='listitem'):
        super().__init__(variable, listitem_type)
        self.containers = containers

    def get_name(self):
        return super().get_name() + '_Parent'

    def get_value(self, container):
        name = super().get_name()
        condition = 'True'
        if container:
            name += f'_C{container}'
            condition = self.variable['parent'].format(id=container)
        return {'tag': 'value', 'attrib': {'condition': condition}, 'content': f'$VAR[{name}]'}

    def get_content(self):
        return [self.get_value(container) for container in self.containers]
