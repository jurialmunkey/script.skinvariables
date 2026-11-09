# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from json import loads
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import load_filecontent


PROPERTY_PREFIX = 'SkinVariables.SkinSettings'
CATEGORY_PROPERTY = f'{PROPERTY_PREFIX}.Category'

# Category ids match Kodi's native category buttons so skin navigation such as SetFocus(-200) still works.
CATEGORY_ID_START = -200
GROUP_ID_START = -100000
SETTING_ID_START = -200000


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

    def onstep(self, window, direction):
        pass

    def oninit(self, window):
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
        window.setProperty(CATEGORY_PROPERTY, self.key)
        super().onfocus(window)


class SettingsListItem(DefinitionItem):
    """Item shown in the settings grouplist only while its category is selected."""

    @property
    def category(self):
        raise NotImplementedError

    @cached_property
    def visible(self):
        return self.get_visible()

    def get_visible(self):
        conditions = [self.category.condition] + ([self.meta['visible']] if 'visible' in self.meta else [])
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


class SettingValue:
    def __init__(self, key, meta, rank):
        self.key = key
        self.meta = meta
        self.rank = rank

    @property
    def label(self):
        return str(self.meta.get('label', ''))

    @property
    def value(self):
        return str(self.meta.get('value', ''))

    @cached_property
    def quoted_value(self):
        return self.get_quoted_value()

    def get_quoted_value(self):
        escaped = self.value.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'

    def get_builtin(self, skinstring):
        # Skin.SetString with an empty value opens the keyboard so an empty value resets the string instead.
        if not self.value:
            return f'Skin.Reset({skinstring})'
        return f'Skin.SetString({skinstring},{self.quoted_value})'

    def apply(self, skinstring):
        xbmc.executebuiltin(self.get_builtin(skinstring), True)


class ValueSetting(SkinSetting):
    """Setting that steps through values stored in a skin string. Unmatched skin strings select the first value."""

    @property
    def skinstring(self):
        return self.meta['skinstring']

    @cached_property
    def values(self):
        return self.get_values()

    def get_values(self):
        return [
            SettingValue(key, meta, rank)
            for rank, (key, meta) in enumerate(DefinitionEntries(self.meta['values']).entries)
        ]

    @cached_property
    def value_ranks(self):
        return self.get_value_ranks()

    def get_value_ranks(self):
        return {value.value: value.rank for value in reversed(self.values)}

    @property
    def current_value(self):
        return xbmc.getInfoLabel(f'Skin.String({self.skinstring})')

    @property
    def current_rank(self):
        return self.value_ranks.get(self.current_value, 0)

    @cached_property
    def label_property(self):
        return f'{PROPERTY_PREFIX}.{self.key}.Label'

    @cached_property
    def value_property(self):
        return f'{PROPERTY_PREFIX}.{self.key}.Value'

    @cached_property
    def default_label2(self):
        return f'$INFO[Window.Property({self.label_property})]'

    def get_optional_overrides(self):
        label2 = [] if 'label2' in self.meta else [('label2', self.default_label2, {})]
        return super().get_optional_overrides() + label2

    def get_overrides(self):
        # Left and right step through values so they must not move focus away from the control.
        return super().get_overrides() + [('onleft', 'noop', {}), ('onright', 'noop', {})]

    def get_stepped_rank(self, direction):
        raise NotImplementedError

    def update(self, window, value):
        window.setProperty(self.label_property, value.label)
        window.setProperty(self.value_property, value.value)

    def step(self, window, direction):
        value = self.values[self.get_stepped_rank(direction)]
        value.apply(self.skinstring)
        self.update(window, value)

    def onstep(self, window, direction):
        self.step(window, direction)

    def oninit(self, window):
        self.update(window, self.values[self.current_rank])


class SpinControlSetting(ValueSetting):
    template = 'spincontrol'

    def get_stepped_rank(self, direction):
        return (self.current_rank + direction) % len(self.values)

    def onclick(self, window):
        self.step(window, 1)


class SliderSetting(ValueSetting):
    template = 'slider'

    @property
    def maximum(self):
        return len(self.values) - 1

    def get_stepped_rank(self, direction):
        return min(max(self.current_rank + direction, 0), self.maximum)

    def update(self, window, value):
        super().update(window, value)
        window.set_slider(self.control_id, value.rank, self.maximum)


SETTING_CLASSES = {
    'button': ButtonSetting,
    'radiobutton': RadioButtonSetting,
    'spincontrol': SpinControlSetting,
    'slider': SliderSetting,
}


class SkinSettingsDefinition:
    def __init__(self, filepath):
        self.filepath = filepath

    @cached_property
    def meta(self):
        return self.get_meta()

    def get_meta(self):
        return loads(str(load_filecontent(self.filepath)))

    def get_entries(self, section):
        return enumerate(DefinitionEntries(self.meta.get(section, {})).entries)

    @cached_property
    def categories(self):
        return self.get_categories()

    def get_categories(self):
        return [SkinSettingsCategory(key, meta, rank) for rank, (key, meta) in self.get_entries('categories')]

    @cached_property
    def categories_by_key(self):
        return {category.key: category for category in self.categories}

    @cached_property
    def groups(self):
        return self.get_groups()

    def get_groups(self):
        return [
            SkinSettingsGroup(key, meta, rank, self.categories_by_key[meta['category']])
            for rank, (key, meta) in self.get_entries('groups')
        ]

    @cached_property
    def groups_by_key(self):
        return {group.key: group for group in self.groups}

    @cached_property
    def settings(self):
        return self.get_settings()

    def get_settings(self):
        return [
            SETTING_CLASSES[meta['control']](key, meta, rank, self.groups_by_key[meta['group']])
            for rank, (key, meta) in self.get_entries('settings')
        ]

    @cached_property
    def layout(self):
        """Group labels followed by their settings, ordered by category, group and setting."""
        return self.get_layout()

    def get_layout(self):
        return sorted(self.groups + self.settings, key=lambda item: item.order)

    @cached_property
    def controls(self):
        return self.get_controls()

    def get_controls(self):
        return {item.control_id: item for item in self.categories + self.groups + self.settings}
