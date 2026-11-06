# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import re
import xml.etree.ElementTree as ET
from os.path import splitext
from xml.dom import minidom
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import load_filecontent, make_hash, write_skinfile


PROFILE_SETTING = 'script-skinvariables-kodiprofile'


class ProfileIncludes:
    """Keep generated includes separate while retaining the skin's include filename."""

    def __init__(self, folder, filename, profilename):
        self.folder = folder
        self.filename = filename
        self.profilename = profilename

    @cached_property
    def profilehash(self):
        return self.get_profilehash()

    def get_profilehash(self):
        return make_hash(self.profilename)

    @cached_property
    def fileparts(self):
        return self.get_fileparts()

    def get_fileparts(self):
        return splitext(self.filename)

    @cached_property
    def profile_filename(self):
        return self.get_profile_filename()

    def get_profile_filename(self):
        stem, extension = self.fileparts
        return f'{stem}-kodiprofile-{self.profilehash}{extension}'

    @cached_property
    def condition(self):
        return self.get_condition()

    def get_condition(self):
        # Kodi parses operators and infolabels even inside quoted parameters.
        if re.search(r'[.()\[\]|+!$\t\r\n]', self.profilename):
            return f'String.IsEqual(Skin.String({PROFILE_SETTING}),{self.profilehash})'
        name = self.profilename.replace('\\', '\\\\').replace('"', '\\"')
        return f'String.IsEqual(System.ProfileName,"{name}")'

    @cached_property
    def filepath(self):
        return self.get_filepath()

    def get_filepath(self):
        return f'special://skin/{self.folder}/{self.profile_filename}'

    @cached_property
    def dispatcher_filepath(self):
        return self.get_dispatcher_filepath()

    def get_dispatcher_filepath(self):
        return f'special://skin/{self.folder}/{self.filename}'

    @cached_property
    def file_pattern(self):
        return self.get_file_pattern()

    def get_file_pattern(self):
        stem, extension = self.fileparts
        return re.compile(f'{re.escape(stem)}-kodiprofile-[0-9a-f]{{32}}{re.escape(extension)}')

    def update_dispatcher(self):
        content = load_filecontent(self.dispatcher_filepath)
        dispatcher = ProfileIncludeDispatcher(content, self)
        if dispatcher.content == content:
            return False
        write_skinfile(folders=[self.folder], filename=self.filename, content=dispatcher.content)
        if load_filecontent(self.dispatcher_filepath) != dispatcher.content:
            raise OSError(f'Failed to write include dispatcher: {self.dispatcher_filepath}')
        return True


class ProfileIncludeDispatcher:
    def __init__(self, content, output):
        self.source = content
        self.output = output

    @cached_property
    def source_entries(self):
        return self.get_source_entries()

    def get_source_entries(self):
        if not self.source:
            return {}
        root = ET.fromstring(self.source)
        if root.tag != 'includes':
            raise ValueError(f'Expected <includes> in {self.output.dispatcher_filepath}')
        # Legacy output contains definitions; only retain profile dispatcher entries.
        return {
            entry.attrib['file']: entry.attrib['condition']
            for entry in root.findall('include')
            if self.output.file_pattern.fullmatch(entry.get('file', ''))
        }

    @cached_property
    def other_entries(self):
        return self.get_other_entries()

    def get_other_entries(self):
        # A case-only profile rename must not load both the old and new files.
        return {
            filename: condition
            for filename, condition in self.source_entries.items()
            if condition.lower() != self.output.condition.lower()
        }

    @cached_property
    def entries(self):
        return self.get_entries()

    def get_entries(self):
        return {**self.other_entries, self.output.profile_filename: self.output.condition}

    @cached_property
    def content(self):
        return self.get_content()

    def get_content(self):
        root = ET.Element('includes')
        root.extend(
            ET.Element('include', file=filename, condition=condition)
            for filename, condition in sorted(self.entries.items())
        )
        document = minidom.parseString(ET.tostring(root, encoding='utf-8'))
        return document.toprettyxml(indent=' ' * 4, encoding='UTF-8').decode('utf-8')
