# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property


class ScriptWindowItem:
    """Control generated from a template control in a scripted window.

    Overrides replace the template tags. Defaults are only added when the template does not define the tag.
    Substitutions are the values for $SUBSTITUTE[name] in the template text.
    """

    control_id_start = 0
    template = None
    default_tags = ('label', 'label2', 'hinttext')

    @property
    def control_id(self):
        return self.control_id_start + self.rank

    @cached_property
    def values(self):
        """String values of the item by name."""
        return self.get_values()

    def get_values(self):
        raise NotImplementedError

    @cached_property
    def overrides(self):
        return self.get_overrides()

    def get_overrides(self):
        return []

    @cached_property
    def defaults(self):
        return self.get_defaults()

    def get_defaults(self):
        return [
            (tag, self.values[tag], {})
            for tag in self.default_tags
            if tag in self.values
        ]

    @cached_property
    def substitutions(self):
        return self.get_substitutions()

    def get_substitutions(self):
        return self.values

    def onfocus(self, window):
        pass

    def onclick(self, window):
        pass
