# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property


class ViewTypeAssignments:
    def __init__(self, viewtypes, preferences):
        self.viewtypes = viewtypes
        self.preferences = preferences
        self.groups = {viewid: {} for viewid in viewtypes}

    @cached_property
    def assignments(self):
        return self.get_assignments()

    def get_assignments(self):
        return [
            (location, contentid, viewid)
            for location, rules in self.preferences.items()
            for contentid, viewid in rules.items()
        ]

    def add_plugin(self, location, contentid, viewid):
        for current, content in self.groups.items():
            listtype = 'whitelist' if current == viewid else 'blacklist'
            content.setdefault(contentid, {}).setdefault(listtype, []).append(location)

    def add_assignment(self, location, contentid, viewid):
        try:
            target = self.groups[viewid]
        except KeyError:
            return
        if location in ('library', 'plugins'):
            target.setdefault(contentid, {}).setdefault(location, True)
            return
        self.add_plugin(location, contentid, viewid)

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        for location, contentid, viewid in self.assignments:
            self.add_assignment(location, contentid, viewid)
        return self.groups


class ViewContentExpression:
    def __init__(self, rules, contentid, flags):
        self.rules = rules
        self.contentid = contentid
        self.flags = flags

    @cached_property
    def rule(self):
        return self.get_rule()

    def get_rule(self):
        return self.rules.get(self.contentid, {}).get('rule')

    @cached_property
    def whitelist(self):
        return self.get_whitelist()

    def get_whitelist(self):
        conditions = ['String.IsEmpty(Container.PluginName)'] if self.flags.get('library') else []
        conditions.extend(f'String.IsEqual(Container.PluginName,{name})' for name in self.flags.get('whitelist', []))
        return ' | '.join(conditions)

    @cached_property
    def blacklist(self):
        return self.get_blacklist()

    def get_blacklist(self):
        if not self.flags.get('plugins'):
            return ''
        conditions = ['!String.IsEmpty(Container.PluginName)']
        conditions.extend(f'!String.IsEqual(Container.PluginName,{name})' for name in self.flags.get('blacklist', []))
        return ' + '.join(conditions)

    @cached_property
    def affix(self):
        return self.get_affix()

    def get_affix(self):
        if self.whitelist and self.blacklist:
            return f'[{self.whitelist}] | [{self.blacklist}]'
        return self.whitelist or self.blacklist

    @cached_property
    def expression(self):
        return self.get_expression()

    def get_expression(self):
        rule = self.rule
        return f'[{rule} + [{self.affix}]]' if self.affix else ''


class ViewTypeExpression:
    def __init__(self, viewid, meta, groups):
        self.viewid = viewid
        self.meta = meta
        self.groups = groups

    @cached_property
    def expression(self):
        return self.get_expression()

    def get_expression(self):
        expressions = (
            ViewContentExpression(self.meta.get('rules', {}), contentid, flags).expression
            for contentid, flags in self.groups.items()
        )
        return ' | '.join(expression for expression in expressions if expression)


class ConditionalViewTypeExpression(ViewTypeExpression):
    def get_expression(self):
        expression = super().get_expression()
        rules = [
            f'[{rule.get("rule")}]'
            for rule in self.meta.get('rules', {}).values()
            if self.viewid in rule.get('viewtypes', [])
        ]
        condition = self.meta.get('condition')
        rule_cond = f'![{condition}] + [{" | ".join(rules)}]'
        rule_expr = f'[{condition}] + [{expression}]'
        return f'[{rule_expr}] | [{rule_cond}]'


class ViewTypeExpressions:
    def __init__(self, meta, assignments):
        self.meta = meta
        self.assignments = assignments

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        expression_class = ConditionalViewTypeExpression if self.meta.get('condition') else ViewTypeExpression
        return {
            viewid: expression_class(viewid, self.meta, groups).expression
            for viewid, groups in self.assignments.items()
        }


class ViewTypeXML:
    def __init__(self, name, content, prefix):
        self.name = name
        self.source = content
        self.prefix = prefix

    @cached_property
    def content(self):
        return self.get_content()

    def get_content(self):
        content = self.source.replace('[]', '[False]') if self.source else 'False'
        return f'[{content}]'

    @cached_property
    def include(self):
        return self.get_include()

    def get_include(self):
        return 'True' if self.source else 'False'

    @cached_property
    def result(self):
        return self.get_result()

    def get_result(self):
        return [
            {'tag': 'expression', 'attrib': {'name': self.prefix + self.name}, 'content': self.content},
            {'tag': 'expression', 'attrib': {'name': self.prefix + self.name + '_Include'}, 'content': self.include},
        ]


class ViewTypesXML:
    def __init__(self, expressions, prefix):
        self.expressions = expressions
        self.prefix = prefix

    @cached_property
    def xmltree(self):
        return self.get_xmltree()

    def get_xmltree(self):
        return [
            element
            for name, content in self.expressions.items()
            for element in ViewTypeXML(name, content, self.prefix).result
        ]
