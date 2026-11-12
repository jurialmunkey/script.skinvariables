# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import re
from urllib.parse import quote
from jurialmunkey.ftools import cached_property


QUERY_PATTERN = re.compile(r'\{(query|query_double|query_raw)\}')


class SearchQuery:
    """Search text with the encodings that search paths can use.

    {query} is percent encoded, {query_double} is percent encoded twice and {query_raw} is not encoded.
    """

    def __init__(self, text):
        self.text = text

    @cached_property
    def raw(self):
        return self.get_raw()

    def get_raw(self):
        return self.text.strip()

    @cached_property
    def encoded(self):
        return self.get_encoded()

    def get_encoded(self):
        return quote(self.raw, safe='')

    @cached_property
    def double_encoded(self):
        return self.get_double_encoded()

    def get_double_encoded(self):
        return quote(self.encoded, safe='')

    @cached_property
    def values(self):
        return self.get_values()

    def get_values(self):
        return {
            'query': self.encoded,
            'query_double': self.double_encoded,
            'query_raw': self.raw,
        }

    def format(self, template):
        """Replace only the query placeholders so other braces in the path are kept."""
        return QUERY_PATTERN.sub(lambda match: self.values[match.group(1)], template)
