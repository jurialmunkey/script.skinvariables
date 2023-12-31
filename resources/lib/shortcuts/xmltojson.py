# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xml.etree.ElementTree as ET


"""
Module for converting xml based template config code into json
"""


class Meta():
    def __init__(self, root, meta):
        self.root = root
        self.meta = meta

    def set_listtext(self, tag, key=None):
        """
        XML:
        <datafile>D1</datafile>
        <datafile>D2</datafile>
        <condition>C1</condition>
        <condition>C2</condition>

        JSON:
        {
            "datafile": [
                "D1",
                "D2"
            ],
            "condition": [
                "C1",
                "C2"
            ]
        }
        """
        value = [i.text for i in self.root.findall(tag)]
        if not value:
            return
        self.meta[key or tag] = value
        return value

    def set_itemtext(self, tag, key=None):
        """
        XML:
        <template>T1</template>

        JSON:
        {
            "template": "T1"
        }
        """
        value = next((i.text for i in self.root.findall(tag) if i.text), None)
        if not value:
            return
        self.meta[key or tag] = value
        return value

    def set_value(self):
        """
        XML:
        <value name="N1">
            C1
        </value>

        JSON:
        {
            "N1": {
                C1
            }
        }
        """
        values = []
        for root in self.root.findall('value'):
            name = root.attrib['name'] if 'name' in root.attrib else 'value'
            if not list(root):
                self.meta[name] = root.text
                continue
            values.append(Meta(root, self.meta.setdefault(name, {})))
        return values

    def set_items(self):
        """
        XML:
        <items node="N1" mode="M1" item="I1">
            <item>
                C1
            </item>
            <item>
                C2
            </item>
        </items>

        JSON:
        {
            "node": "N1",
            "mode": "M1",
            "item": "I1",
            "for_each" [
                {
                    C1
                },
                {
                    C2
                }
            ]
        }
        """
        root = next((i for i in self.root.findall('items')), None)
        if not root:
            return []

        for k, v in root.attrib.items():
            self.meta[k] = v

        items = []
        self.meta['for_each'] = []
        for item in root.findall('item'):
            meta = {}
            self.meta['for_each'].append(meta)
            items.append(Meta(item, meta))
        return items

    def set_lists(self):
        """
        XML:
        <list name="N1">
            <value name="K1">V1</value>
            <value name="K2">V2</value>
        </list>
        <list name="N2">
            <value name="K3">V3</value>
            <value name="K4">V4</value>
        </list>

        JSON:
        {
            "list": [
                ["N1", {"K1": "V1", "K2": "V2"}],
                ["N2", {"K3": "V3", "K4": "V4"}]
            ]
        }
        """
        items = []
        self.meta['list'] = []
        for item in self.root.findall('list'):
            meta = {}
            pair = [item.attrib['name'], meta]
            self.meta['list'].append(pair)
            items.append(Meta(item, meta))
        if not items:
            del self.meta['list']
            return []
        return items

    def set_rules(self):
        """
        XML:
        <variable name="N1">
            <rule>
                <condition>C1</condition>
                <value>V1</value>
            </rule>
            <rule>
                <condition>C2</condition>
                <value>V2</value>
            </rule>
        </variable>

        JSON:
        {
            "N1": [
                {
                    "condition": "C1",
                    "value": "V1"
                },
                {
                    "condition": "C2",
                    "value": "V2"
                }
            ]
        }
        """
        items = []
        for root in self.root.findall('variable'):
            name = root.attrib['name']
            self.meta[name] = []
            for item in root.findall('rule'):
                meta = {}
                self.meta[name].append(meta)
                items.append(Meta(item, meta))
        return items


class XMLtoJSON():
    def __init__(self, filecontent):
        self.root = ET.fromstring(filecontent)
        self.meta = {}

    def get_meta(self):
        self.get_contents(Meta(self.root, self.meta))
        return self.meta

    def get_contents(self, meta):
        meta.set_itemtext('template')
        meta.set_listtext('datafile')
        meta.set_listtext('condition')
        for i in meta.set_rules():
            self.get_contents(i)
        for i in meta.set_value():
            self.get_contents(i)
        for i in meta.set_lists():
            self.get_contents(i)
        for i in meta.set_items():
            self.get_contents(i)


def xml_to_json(filecontent):
    return XMLtoJSON(filecontent).get_meta()
