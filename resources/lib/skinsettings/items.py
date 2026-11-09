# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from jurialmunkey.ftools import cached_property


PROPERTY_PREFIX = 'SkinVariables.SkinSettings'
CATEGORY_PROPERTY = f'{PROPERTY_PREFIX}.Category'
SEARCH_PROPERTY_PREFIX = f'{PROPERTY_PREFIX}.Search'

# Category ids match Kodi's native category buttons so skin navigation such as SetFocus(-200) still works.
CATEGORY_ID_START = -200
GROUP_ID_START = -100000
SETTING_ID_START = -200000


def get_label_text(label):
    """Resolve a skin label to its displayed text. Kodi parses $INFO, $LOCALIZE and $VAR in full labels."""
    if label.isdigit():
        return xbmc.getLocalizedString(int(label))
    if '$' in label:
        return xbmc.getInfoLabel(label)
    return label


class DefinitionEntries:
    """Sorts the keyed entries of a definition section by index, then by declaration order."""

    def __init__(self, meta):
        self.meta = meta

    @staticmethod
    def get_sort_key(position, entry):
        key, meta = entry
        return (int(meta.get('index', position)), position)

    @cached_property
    def entries(self):
        return self.get_entries()

    def get_entries(self):
        return [
            entry
            for position, entry in sorted(enumerate(self.meta.items()), key=lambda item: self.get_sort_key(*item))
        ]


class DefinitionItem:
    control_id_start = 0
    template = None

    def __init__(self, key, meta, rank, parent=None):
        self.key = key
        self.meta = meta
        self.rank = rank
        self.parent = parent

    @property
    def control_id(self):
        return self.control_id_start + self.rank

    @property
    def label(self):
        return str(self.meta.get('label', ''))

    @property
    def description(self):
        return str(self.meta.get('description', ''))

    @property
    def label_text(self):
        return get_label_text(self.label)

    @property
    def description_text(self):
        return get_label_text(self.description)

    @cached_property
    def order(self):
        return self.get_order()

    def get_order(self):
        return self.parent.order + (self.rank,)

    @cached_property
    def overrides(self):
        return self.get_overrides()

    def get_overrides(self):
        return [('label', self.label, {})]

    def onfocus(self, window):
        window.set_description(self.description)

    def onclick(self, window):
        pass


class SkinSettingsCategory(DefinitionItem):
    control_id_start = CATEGORY_ID_START
    template = 'category'

    @cached_property
    def condition(self):
        return self.get_condition()

    def get_condition(self):
        return f'String.IsEqual(Window.Property({CATEGORY_PROPERTY}),{self.key})'

    def get_order(self):
        return (self.rank,)

    def get_overrides(self):
        # Togglebutton templates show the selected category with their alt textures. Other control types ignore the tag.
        return super().get_overrides() + [('usealttexture', self.condition, {})]

    def onfocus(self, window):
        window.set_category(self.key)
        super().onfocus(window)


class SettingsListItem(DefinitionItem):
    """Item shown in the settings grouplist while its category is selected or while it matches the search."""

    def __init__(self, key, meta, rank, parent, search):
        super().__init__(key, meta, rank, parent)
        self.search = search

    @property
    def category(self):
        raise NotImplementedError

    @cached_property
    def search_property(self):
        return f'{SEARCH_PROPERTY_PREFIX}.{self.control_id}'

    @cached_property
    def match_condition(self):
        return self.get_match_condition()

    def get_match_condition(self):
        return f'!String.IsEmpty(Window.Property({self.search_property}))'

    @cached_property
    def shown_condition(self):
        return self.get_shown_condition()

    def get_shown_condition(self):
        return self.search.get_shown_condition(self)

    @cached_property
    def visible(self):
        return self.get_visible()

    def get_visible(self):
        conditions = [self.shown_condition] + ([self.meta['visible']] if 'visible' in self.meta else [])
        return ' + '.join(f'[{condition}]' for condition in conditions)

    def get_overrides(self):
        return super().get_overrides() + [('visible', self.visible, {})]


class SkinSettingsGroup(SettingsListItem):
    control_id_start = GROUP_ID_START
    template = 'group'

    @property
    def category(self):
        return self.parent


class SkinSetting(SettingsListItem):
    control_id_start = SETTING_ID_START
    template = 'button'
    optional_tags = (('label2', 'label2'), ('enabled', 'enable'))

    @property
    def group(self):
        return self.parent

    @property
    def category(self):
        return self.group.category

    @property
    def search_text(self):
        return ' '.join((self.label_text, self.group.label_text, self.description_text)).lower()

    @cached_property
    def focusable_condition(self):
        return self.get_focusable_condition()

    def get_focusable_condition(self):
        conditions = [self.visible] + ([self.meta['enabled']] if 'enabled' in self.meta else [])
        return ' + '.join(f'[{condition}]' for condition in conditions)

    @cached_property
    def optional_overrides(self):
        return self.get_optional_overrides()

    def get_optional_overrides(self):
        return [(tag, str(self.meta[key]), {}) for key, tag in self.optional_tags if key in self.meta]

    def get_overrides(self):
        return super().get_overrides() + self.optional_overrides


class ButtonSetting(SkinSetting):
    template = 'button'

    @staticmethod
    def get_onclick_override(onclick):
        attrib = {'condition': onclick['condition']} if onclick.get('condition') else {}
        return ('onclick', onclick['action'], attrib)

    @cached_property
    def onclick_overrides(self):
        return self.get_onclick_overrides()

    def get_onclick_overrides(self):
        return [self.get_onclick_override(onclick) for onclick in self.meta.get('onclick', [])]

    def get_overrides(self):
        return super().get_overrides() + self.onclick_overrides


class RadioButtonSetting(ButtonSetting):
    template = 'radiobutton'
    optional_tags = SkinSetting.optional_tags + (('selected', 'selected'),)


SETTING_CLASSES = {
    'button': ButtonSetting,
    'radiobutton': RadioButtonSetting,
}
