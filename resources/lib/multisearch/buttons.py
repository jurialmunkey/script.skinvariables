# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.kodiutils import get_localized
from resources.lib.multisearch.constants import PROPERTY_PREFIX
from resources.lib.scriptwindow.items import ScriptWindowItem


SOURCE_ID_START = -400000
SOURCE_PROPERTY = f'{PROPERTY_PREFIX}.Source'


class SourceFilterButton(ScriptWindowItem):
    """Button generated in the source grouplist. Focusing it shows only the results of its source."""

    template = 'button'
    control_id_start = SOURCE_ID_START

    @property
    def label(self):
        raise NotImplementedError

    @cached_property
    def focus_properties(self):
        return self.get_focus_properties()

    def get_focus_properties(self):
        return {SOURCE_PROPERTY: self.label}

    def is_shown(self, sources, view):
        raise NotImplementedError

    def get_results(self, view):
        """Filtered, sorted and limited results shown while the button is selected."""
        raise NotImplementedError

    def get_scope_results(self, view):
        """Unfiltered results that the genre and decade options are taken from while the button is selected."""
        raise NotImplementedError

    def onfocus(self, window):
        window.select_button(self)

    def onaction(self, window, action_id):
        pass


class AllSourcesButton(SourceFilterButton):
    """Button for the results of every enabled source. Always shown first and selected when the window opens."""

    rank = 0

    @cached_property
    def label(self):
        return get_localized(593)

    def get_values(self):
        return {
            'label': self.label,
            'icon': '',
            'target': '',
            'widget_style': '',
        }

    def is_shown(self, sources, view):
        return True

    def get_results(self, view):
        return view.all_items

    def get_scope_results(self, view):
        return view.all_results


class SourceButton(SourceFilterButton):
    """Button for one search source. Shown while the source is enabled and has filtered results."""

    def __init__(self, source, position):
        self.source = source
        self.position = position

    @property
    def rank(self):
        return self.position + 1

    @property
    def label(self):
        return self.source.label

    @cached_property
    def shown_property(self):
        return f'{SOURCE_PROPERTY}.{self.position}.HasResults'

    def get_values(self):
        return {
            'label': self.source.label,
            'icon': self.source.icon,
            'target': self.source.target,
            'widget_style': self.source.widget_style,
        }

    def get_overrides(self):
        return [('visible', f'!String.IsEmpty(Window.Property({self.shown_property}))', {})]

    def is_shown(self, sources, view):
        # Sources turned off since the search started are hidden before the next search finishes.
        return self.source in sources.enabled and view.has_results(self.source)

    def get_results(self, view):
        return view.get_source_items(self.source)

    def get_scope_results(self, view):
        return view.get_source_results(self.source)


class SourceButtons:
    """Buttons of the source grouplist: the all sources button followed by a button for each source."""

    def __init__(self, sources):
        self.sources = sources

    @cached_property
    def all_button(self):
        return AllSourcesButton()

    @cached_property
    def source_buttons(self):
        return self.get_source_buttons()

    def get_source_buttons(self):
        return [SourceButton(source, position) for position, source in enumerate(self.sources.items)]

    @cached_property
    def items(self):
        return [self.all_button, *self.source_buttons]

    @cached_property
    def controls(self):
        return self.get_controls()

    def get_controls(self):
        return {button.control_id: button for button in self.items}

    def get_shown_properties(self, view):
        """Window properties that show the buttons of the enabled sources with filtered results."""
        return {
            button.shown_property: 'true' if button.is_shown(self.sources, view) else ''
            for button in self.source_buttons
        }
