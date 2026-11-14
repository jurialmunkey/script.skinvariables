# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property
from resources.lib.kodiutils import get_localized
from resources.lib.multisearch.constants import PROPERTY_PREFIX
from resources.lib.multisearch.filters import MediaTypeFilter, OTHER_MEDIATYPE
from resources.lib.scriptwindow.items import ScriptWindowItem


SOURCE_ID_START = -400000
SOURCE_PROPERTY = f'{PROPERTY_PREFIX}.Source'
MEDIATYPE_PLURAL_LOCALIZED_IDS = {
    'movie': 342,
    'set': 20434,
    'tvshow': 20343,
    'season': 33054,
    'episode': 20360,
    'musicvideo': 20389,
    'artist': 133,
    'album': 132,
    'song': 134,
    OTHER_MEDIATYPE: 32103,
}


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

    def get_values(self):
        return {
            'label': self.label,
            'icon': '',
            'target': '',
            'widget_style': '',
        }

    def is_shown(self, sources, view):
        raise NotImplementedError

    def repeats_all(self, sources, view):
        """Whether the button is shown with the same results as the all sources button."""
        return False

    def get_results(self, view):
        """Filtered, sorted and limited results shown while the button is selected."""
        raise NotImplementedError

    def get_container_choice(self, containers, results):
        """Container for the results shown while the button is selected."""
        return containers.get_choice(results)

    def onfocus(self, window):
        window.select_button(self)

    def onclick(self, window):
        window.select_source_button()

    def onaction(self, window, action_id):
        pass


class ToggledSourceFilterButton(SourceFilterButton):
    """Button that is only visible while its window property is set."""

    @cached_property
    def shown_property(self):
        return self.get_shown_property()

    def get_shown_property(self):
        raise NotImplementedError

    def get_overrides(self):
        return [('visible', f'!String.IsEmpty(Window.Property({self.shown_property}))', {})]


class AllSourcesButton(ToggledSourceFilterButton):
    """Button for the results of every enabled source. Always listed first.

    Hidden while another button shows the same results, so that button is shown instead of repeating them.
    """

    rank = 0

    def __init__(self, buttons):
        self.buttons = buttons

    @cached_property
    def label(self):
        return get_localized(593)

    def get_shown_property(self):
        return f'{SOURCE_PROPERTY}.All.IsShown'

    def is_shown(self, sources, view):
        return not any(button.repeats_all(sources, view) for button in self.buttons)

    def get_results(self, view):
        return view.all_items


class MediaTypeSourcesButton(ToggledSourceFilterButton):
    """Button for the results of every enabled source with one content type.

    Shown while any of the all sources results have the content type. Shown instead of the all sources button while
    every one of them has the content type.
    """

    def __init__(self, mediatype, rank):
        self.mediatype = mediatype
        self.rank = rank

    @cached_property
    def result_filter(self):
        return self.get_result_filter()

    def get_result_filter(self):
        result_filter = MediaTypeFilter()
        result_filter.set_value(self.mediatype)
        return result_filter

    @cached_property
    def label(self):
        return get_localized(MEDIATYPE_PLURAL_LOCALIZED_IDS[self.mediatype])

    def get_shown_property(self):
        return f'{SOURCE_PROPERTY}.{self.result_filter.property_affix}.{self.mediatype}.HasResults'

    def is_shown(self, sources, view):
        return view.has_mediatype(self.result_filter)

    def repeats_all(self, sources, view):
        return view.has_only_mediatype(self.result_filter)

    def get_results(self, view):
        return view.get_mediatype_items(self.result_filter)

    def get_container_choice(self, containers, results):
        """The results use the widget style of the content type when the skin defines one."""
        return containers.get_mediatype_choice(self.mediatype, results)


class SourceButton(ToggledSourceFilterButton):
    """Button for one search source. Shown while the source is enabled and has filtered results.

    Shown instead of the all sources button while it is the only source with filtered results.
    """

    def __init__(self, source, position):
        self.source = source
        self.position = position

    @property
    def rank(self):
        return self.position + 1

    @property
    def label(self):
        return self.source.label

    def get_shown_property(self):
        return f'{SOURCE_PROPERTY}.{self.position}.HasResults'

    def get_values(self):
        return {
            'label': self.source.label,
            'icon': self.source.icon,
            'target': self.source.target,
            'widget_style': self.source.widget_style,
        }

    def is_shown(self, sources, view):
        # Sources turned off since the search started are hidden before the next search finishes.
        return self.source in sources.enabled and view.has_results(self.source)

    def repeats_all(self, sources, view):
        return self.source in sources.enabled and view.has_only_source(self.source)

    def get_results(self, view):
        return view.get_source_items(self.source)


class SourceButtons:
    """Buttons of the source grouplist.

    The all sources button is followed by a button for each content type and then a button for each source. The
    content type buttons are ranked after the source buttons to keep the control ids of the source buttons.
    The all sources button is hidden while one of the other buttons shows the same results.
    """

    def __init__(self, sources):
        self.sources = sources

    @cached_property
    def all_button(self):
        return AllSourcesButton(self.toggled_buttons)

    @cached_property
    def source_buttons(self):
        return self.get_source_buttons()

    def get_source_buttons(self):
        return [SourceButton(source, position) for position, source in enumerate(self.sources.items)]

    @cached_property
    def mediatype_buttons(self):
        return self.get_mediatype_buttons()

    def get_mediatype_buttons(self):
        return [
            MediaTypeSourcesButton(mediatype, rank)
            for rank, mediatype in enumerate(MEDIATYPE_PLURAL_LOCALIZED_IDS, len(self.source_buttons) + 1)
        ]

    @cached_property
    def toggled_buttons(self):
        return [*self.mediatype_buttons, *self.source_buttons]

    @cached_property
    def items(self):
        return [self.all_button, *self.toggled_buttons]

    @cached_property
    def grouplist_items(self):
        """Buttons generated in the source grouplist."""
        return self.get_grouplist_items()

    def get_grouplist_items(self):
        return self.items

    @cached_property
    def controls(self):
        return self.get_controls()

    def get_controls(self):
        return {button.control_id: button for button in self.grouplist_items}

    def get_shown_properties(self, view):
        """Window properties that show the buttons with results, without two buttons showing the same results."""
        return {
            button.shown_property: 'true' if button.is_shown(self.sources, view) else ''
            for button in self.items
        }

    def get_shown_buttons(self, view):
        """Buttons shown in the grouplist, in grouplist order."""
        return [button for button in self.items if button.is_shown(self.sources, view)]

    def get_default_button(self, view):
        """First shown button, selected when the window opens or when the selected button is hidden.

        The all sources button is shown unless another button shows its results, so a button is always shown.
        """
        return next(button for button in self.items if button.is_shown(self.sources, view))


class MediaTypeButtons(SourceButtons):
    """Buttons of the source grouplist without a button for each source.

    The all sources button is followed by a button for each content type.
    """

    @cached_property
    def toggled_buttons(self):
        return self.mediatype_buttons


class NoGrouplistButtons(SourceButtons):
    """Source buttons without the source grouplist, for windows with a list for each content type.

    The all sources button is the only button and is always selected. The content type buttons supply the results of
    the content type lists. The all sources button is hidden while a content type list shows the same results.
    """

    @cached_property
    def all_button(self):
        return AllSourcesButton(self.mediatype_buttons)

    @cached_property
    def toggled_buttons(self):
        return []

    def get_grouplist_items(self):
        return []

    def get_default_button(self, view):
        return self.all_button
