import re
import xbmc


class RuleOperations():
    def __init__(self, meta, **params):
        self.meta = meta
        self.params = params
        self.run_operations()

    def run_operations(self):
        for i in self.operations:
            for k, v in i.items():
                self.routes[k](v)

    @property
    def operations(self):
        return [{i: self.meta[i]} for i in self.routes if i in self.meta] + self.meta.get('operations', [])

    @property
    def routes(self):
        try:
            return self._routes
        except AttributeError:
            self._routes = {
                'infolabels': self.set_infolabels,
                'regex': self.set_regex,
                'values': self.set_values,
                'sums': self.set_sums,
                'decode': self.set_decode,
                'encode': self.set_encode,
                'escape': self.set_escape,
                'lower': self.set_lower,
                'upper': self.set_upper,
                'capitalize': self.set_capitalize,
            }
            return self._routes

    def set_infolabels(self, d):
        for k, v in d.items():
            k = k.format(**self.params)
            v = v.format(**self.params)
            self.params[k] = xbmc.getInfoLabel(v)

    def set_regex(self, d):
        for k, v in d.items():
            k = k.format(**self.params)
            self.params[k] = re.sub(v['regex'].format(**self.params), v['value'].format(**self.params), v['input'].format(**self.params))

    def set_values(self, d):
        for k, v in d.items():
            k = k.format(**self.params)
            self.params[k] = self.get_actions_list(v)[0]

    def set_sums(self, d):
        for k, v in d.items():
            k = k.format(**self.params)
            self.params[k] = sum([int(i.format(**self.params)) for i in v])

    def set_decode(self, d):
        from urllib.parse import unquote_plus
        for k, v in d.items():
            k = k.format(**self.params)
            v = v.format(**self.params)
            self.params[k] = unquote_plus(v)

    def set_encode(self, d):
        from urllib.parse import quote_plus
        for k, v in d.items():
            k = k.format(**self.params)
            v = v.format(**self.params)
            self.params[k] = quote_plus(v)

    def set_escape(self, d):
        from xml.sax.saxutils import escape
        for k, v in d.items():
            k = k.format(**self.params)
            v = v.format(**self.params)
            self.params[k] = escape(v)

    def set_lower(self, d):
        for k, v in d.items():
            k = k.format(**self.params)
            self.params[k] = v.format(**self.params).lower()

    def set_upper(self, d):
        for k, v in d.items():
            k = k.format(**self.params)
            self.params[k] = v.format(**self.params).upper()

    def set_capitalize(self, d):
        for k, v in d.items():
            k = k.format(**self.params)
            self.params[k] = v.format(**self.params).capitalize()

    def check_rules(self, rules):
        result = True
        for rule in rules:
            # Rules can have sublists of rules
            if isinstance(rule, list):
                result = self.check_rules(rule)
                if not result:
                    continue
                return True
            rule = rule.format(**self.params)
            if not xbmc.getCondVisibility(rule):
                return False
        return result

    def get_actions_list(self, rule_actions):
        actions_list = []

        if not isinstance(rule_actions, list):
            rule_actions = [rule_actions]

        for action in rule_actions:

            # Parts are prefixed with percent % so needs to be replaced
            if isinstance(action, str) and action.startswith('%'):
                action = action.format(**self.params)
                action = self.meta['parts'][action[1:]]

            # Standard actions are strings - add formatted action to list and continue
            if isinstance(action, str):
                actions_list.append(action.format(**self.params))
                continue

            # Sublists of actions are lists - recursively add sublists and continue
            if isinstance(action, list):
                actions_list += self.get_actions_list(action)
                continue

            # Rules are dictionaries - successful rules add their actions and stop iterating (like a skin variable)
            if self.check_rules(action['rules']):
                actions_list += self.get_actions_list(action['value'])
                break

        return actions_list
