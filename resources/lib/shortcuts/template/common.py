# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import re
from xml.dom import minidom


SKIN_BASEDIR = 'special://skin'
SHORTCUTS_FOLDER = 'shortcuts'


def escape_ampersands(myxml):
    regex = re.compile(r"&(?!amp;|lt;|gt;)")
    return regex.sub("&amp;", myxml)


def pretty_xmlcontent(myxml):
    myxml = minidom.parseString(myxml)
    return '\n'.join([line for line in myxml.toprettyxml(indent=' ' * 4).split('\n') if line.strip()])


class FormatDict(dict):
    def __missing__(self, key):
        if key.endswith('_escaped'):
            return self[key[:-8]]
        return ''
