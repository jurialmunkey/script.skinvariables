# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html


def get_paramstring_tuplepairs(paramstring):
    if not paramstring:
        return []
    return [tuple(item.split(';')) for item in paramstring.split(';;')]
