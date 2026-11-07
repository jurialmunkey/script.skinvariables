# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property


XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>'


class XMLNode:
    def __init__(self, meta, indent, indentation):
        self.meta = meta
        self.indent = indent
        self.indentation = indentation

    @property
    def tag(self):
        return self.meta.get('tag', '')

    @property
    def content(self):
        return self.meta.get('content')

    @cached_property
    def attributes(self):
        return self.get_attributes()

    def get_attributes(self):
        return [(key, value) for key, value in self.meta.get('attrib', {}).items() if key]

    @cached_property
    def opening_parts(self):
        return self.get_opening_parts()

    def get_opening_parts(self):
        attributes = [f' {key}="{value}"' for key, value in self.attributes]
        ending = '>' if self.content else '/>'
        return ['\n', self.indentation, f'<{self.tag}'] + attributes + [ending]

    @cached_property
    def content_parts(self):
        return self.get_content_parts()

    def get_content_parts(self):
        if not self.content:
            return []
        if isinstance(self.content, list):
            # Nested lists retain default spacing and do not report progress.
            content = [XMLTree(self.content, self.indent + 1).text, '\n', self.indentation]
        else:
            content = [self.content]
        return content + [f'</{self.tag}>']


class XMLTree:
    def __init__(self, source, indent=1, indent_spaces=4):
        self.source = source
        self.indent = indent
        self.indent_spaces = indent_spaces

    @cached_property
    def indentation(self):
        return self.get_indentation()

    def get_indentation(self):
        return ' ' * self.indent_spaces * self.indent

    def report_node(self, index, node):
        pass

    @cached_property
    def parts(self):
        return self.get_parts()

    def get_parts(self):
        indentation = self.indentation
        parts = []
        for index, meta in enumerate(self.source):
            node = XMLNode(meta, self.indent, indentation)
            if not node.tag:
                continue
            parts.extend(node.opening_parts)
            self.report_node(index, node)
            parts.extend(node.content_parts)
        return parts

    @cached_property
    def text(self):
        return self.get_text()

    def get_text(self):
        return ''.join(self.parts)


class ProgressXMLTree(XMLTree):
    def __init__(self, source, dialog, indent=1, indent_spaces=4):
        super().__init__(source, indent, indent_spaces)
        self.dialog = dialog
        self.total = len(source)
        self.message = ''

    def report_node(self, index, node):
        if node.attributes:
            self.message = node.attributes[-1][1]
        if node.content:
            self.dialog.update(index * 100 // self.total, message=f'{self.message}')


class XMLIncludes:
    def __init__(self, source, dialog=None):
        self.source = source
        self.dialog = dialog

    @cached_property
    def body(self):
        return self.get_body()

    def get_body(self):
        return make_xml_itertxt(self.source, p_dialog=self.dialog)

    @cached_property
    def text(self):
        return self.get_text()

    def get_text(self):
        return '\n'.join((XML_HEADER, '<includes>', self.body, '</includes>'))


def make_xml_itertxt(xmltree, indent=1, indent_spaces=4, p_dialog=None):
    if p_dialog:
        return ProgressXMLTree(xmltree, p_dialog, indent, indent_spaces).text
    return XMLTree(xmltree, indent, indent_spaces).text


def make_xml_includes(lines=(), p_dialog=None):
    return XMLIncludes(lines, p_dialog).text
