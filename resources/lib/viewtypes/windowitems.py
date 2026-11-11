# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from jurialmunkey.ftools import cached_property


PROPERTY_PREFIX = 'SkinVariables.ViewTypes'
NAME_PROPERTY = f'{PROPERTY_PREFIX}.Name'
SCREENSHOT_PROPERTY = f'{PROPERTY_PREFIX}.Screenshot'
VIEWID_PROPERTY = f'{PROPERTY_PREFIX}.ViewID'
TOTAL_PROPERTY = f'{PROPERTY_PREFIX}.Total'
HEADER_PROPERTY = f'{PROPERTY_PREFIX}.Header'
GROUP_PROPERTY_PREFIX = f'{PROPERTY_PREFIX}.Group'

GROUP_ID_START = -100000
VIEW_ID_START = -200000


class ViewTypesWindowItem:
    """Button generated in the selector dialog for a viewtype or a group of viewtypes."""

    control_id_start = 0
    template = None

    def __init__(self, source, rank):
        self.source = source
        self.rank = rank

    @property
    def control_id(self):
        return self.control_id_start + self.rank

    @property
    def name(self):
        return self.source.name

    @property
    def icon(self):
        return self.source.icon

    @property
    def view_id(self):
        """Viewtype of the button. Empty for group buttons so focusing them clears the property."""
        return ''

    @cached_property
    def focus_properties(self):
        return self.get_focus_properties()

    def get_focus_properties(self):
        return {NAME_PROPERTY: self.name, SCREENSHOT_PROPERTY: self.icon, VIEWID_PROPERTY: self.view_id}

    @cached_property
    def overrides(self):
        return self.get_overrides()

    def get_overrides(self):
        return [('label', self.name, {})]

    def onfocus(self, window):
        window.set_properties(self.focus_properties)

    def onclick(self, window):
        pass


class ViewTypesWindowView(ViewTypesWindowItem):
    control_id_start = VIEW_ID_START
    template = 'view'

    def __init__(self, source, rank, current_viewid):
        super().__init__(source, rank)
        self.current_viewid = current_viewid

    @property
    def view_id(self):
        return self.source.view_id

    @cached_property
    def is_current(self):
        return self.view_id == self.current_viewid

    def get_overrides(self):
        return super().get_overrides() + [('selected', str(self.is_current).lower(), {})]

    def onclick(self, window):
        window.select(self)


class ViewTypesWindowGroupedView(ViewTypesWindowView):
    """Viewtype button in a group. The group decides when the button is shown."""

    def __init__(self, source, rank, current_viewid, group):
        super().__init__(source, rank, current_viewid)
        self.group = group

    def get_overrides(self):
        return super().get_overrides() + self.group.view_overrides


class ViewTypesWindowGroup(ViewTypesWindowItem):
    control_id_start = GROUP_ID_START
    template = 'group'

    @cached_property
    def property_prefix(self):
        return f'{GROUP_PROPERTY_PREFIX}.{self.rank}'

    @cached_property
    def expanded_property(self):
        return f'{self.property_prefix}.Expanded'

    @cached_property
    def total_property(self):
        return f'{self.property_prefix}.Total'

    @cached_property
    def expanded_condition(self):
        return f'String.IsEqual(Window.Property({self.expanded_property}),True)'

    @cached_property
    def total(self):
        return len(self.source.items)

    @cached_property
    def state_overrides(self):
        return self.get_state_overrides()

    def get_state_overrides(self):
        # The radiobutton shows whether the group is expanded rather than toggling its own state when clicked.
        return [('selected', self.expanded_condition, {})]

    @cached_property
    def view_overrides(self):
        """Overrides for the viewtype buttons of the group. They are shown while the group is expanded."""
        return self.get_view_overrides()

    def get_view_overrides(self):
        return [('visible', self.expanded_condition, {})]

    def get_overrides(self):
        return super().get_overrides() + self.state_overrides

    def onclick(self, window):
        window.toggle_group(self)


class ViewTypesWindowGroupLabel(ViewTypesWindowGroup):
    """Label heading a group that is always expanded so its viewtype buttons are always shown."""

    template = 'label'

    def get_state_overrides(self):
        return []

    def get_view_overrides(self):
        return []

    def onclick(self, window):
        pass


class ViewTypesGroupState:
    """Expands and collapses groups by setting the window property that their viewtype buttons are visible with."""

    def __init__(self, groups):
        self.groups = groups

    @staticmethod
    def is_expanded(window, group):
        return window.getProperty(group.expanded_property) == 'True'

    @staticmethod
    def collapse(window, group):
        window.clearProperty(group.expanded_property)

    def expand(self, window, group):
        window.setProperty(group.expanded_property, 'True')

    def toggle(self, window, group):
        if self.is_expanded(window, group):
            return self.collapse(window, group)
        return self.expand(window, group)


class ExclusiveGroupState(ViewTypesGroupState):
    """Only one group is expanded at a time so expanding a group collapses the others."""

    def expand(self, window, group):
        for other in self.groups:
            self.collapse(window, other)
        super().expand(window, group)


class ViewTypesWindowLayout:
    """Viewtype buttons in the order they are shown in the selector dialog."""

    def __init__(self, items, current_viewid, header=''):
        self.items = items
        self.current_viewid = current_viewid
        self.header = header

    @cached_property
    def views(self):
        return self.get_views()

    def get_views(self):
        return tuple(ViewTypesWindowView(item, rank, self.current_viewid) for rank, item in enumerate(self.items))

    @cached_property
    def ordered_items(self):
        return self.get_ordered_items()

    def get_ordered_items(self):
        return self.views

    @cached_property
    def controls(self):
        return self.get_controls()

    def get_controls(self):
        return {item.control_id: item for item in self.ordered_items}

    @cached_property
    def current_view(self):
        return self.get_current_view()

    def get_current_view(self):
        return next((view for view in self.views if view.is_current), None)

    @cached_property
    def focus_item(self):
        """Button focused when the dialog opens. The current viewtype or else the first button."""
        return self.get_focus_item()

    def get_focus_item(self):
        return self.current_view or self.ordered_items[0]

    @cached_property
    def total(self):
        return self.get_total()

    def get_total(self):
        return len({view.view_id for view in self.views})

    @cached_property
    def properties(self):
        """Window properties set when the dialog opens."""
        return self.get_properties()

    def get_properties(self):
        properties = {TOTAL_PROPERTY: str(self.total), HEADER_PROPERTY: self.header}
        properties.update(self.focus_item.focus_properties)
        return properties


class ViewTypesWindowGroupedLayout(ViewTypesWindowLayout):
    """Group buttons each followed by the viewtype buttons that are shown while the group is expanded."""

    group_class = ViewTypesWindowGroup
    group_state_class = ViewTypesGroupState

    def __init__(self, items, current_viewid, header='', configured_groups=()):
        super().__init__(items, current_viewid, header)
        self.configured_groups = configured_groups

    @cached_property
    def groups(self):
        return self.get_groups()

    def get_groups(self):
        return tuple(self.group_class(group, rank) for rank, group in enumerate(self.configured_groups))

    @cached_property
    def group_views(self):
        """Viewtype buttons by group. A viewtype in several groups gets a button in each group."""
        return self.get_group_views()

    def get_group_views(self):
        pairs = [(group, item) for group in self.groups for item in group.source.items]
        views = [
            ViewTypesWindowGroupedView(item, rank, self.current_viewid, group)
            for rank, (group, item) in enumerate(pairs)
        ]
        return {group: tuple(view for view in views if view.group is group) for group in self.groups}

    def get_views(self):
        return tuple(view for views in self.group_views.values() for view in views)

    def get_ordered_items(self):
        return tuple(item for group in self.groups for item in (group, *self.group_views[group]))

    @cached_property
    def group_state(self):
        return self.get_group_state()

    def get_group_state(self):
        return self.group_state_class(self.groups)

    def get_properties(self):
        properties = super().get_properties()
        properties.update({group.total_property: str(group.total) for group in self.groups})
        if self.current_view:
            properties[self.current_view.group.expanded_property] = 'True'
        return properties


class ViewTypesWindowExclusiveLayout(ViewTypesWindowGroupedLayout):
    group_state_class = ExclusiveGroupState


class ViewTypesWindowExpandedLayout(ViewTypesWindowGroupedLayout):
    """Group labels each followed by the viewtype buttons of the group, which are always shown."""

    group_class = ViewTypesWindowGroupLabel

    def get_focus_item(self):
        # Labels cannot be focused so the first viewtype button is focused when no viewtype is current.
        return self.current_view or self.views[0]

    def get_properties(self):
        properties = super().get_properties()
        properties.update({group.expanded_property: 'True' for group in self.groups})
        return properties


# Layouts by the groups option. Groups expand and collapse independently when the option is not given.
GROUP_LAYOUT_CLASSES = {
    'exclusive': ViewTypesWindowExclusiveLayout,
    'expanded': ViewTypesWindowExpandedLayout,
}


def get_viewtypes_window_layout(items, current_viewid, header='', configured_groups=(), group_mode=None):
    if not configured_groups:
        return ViewTypesWindowLayout(items, current_viewid, header)
    layout_class = GROUP_LAYOUT_CLASSES.get(group_mode, ViewTypesWindowGroupedLayout)
    return layout_class(items, current_viewid, header, configured_groups)
