# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html


class SkinSettingsViewState:
    """View of newly opened settings. The skin decides the category and focus."""

    def apply(self, window):
        pass


class SavedViewState(SkinSettingsViewState):
    """View saved when a setting is clicked. The settings show it again with focus on the setting when the window
    initialises, such as after a skin reload."""

    def __init__(self, category, query, tag, properties, focus_id):
        self.category = category
        self.query = query
        self.tag = tag
        self.properties = properties
        self.focus_id = focus_id

    def apply(self, window):
        window.restore_view(self.category, self.query, self.tag, self.properties)
        window.setFocusId(self.focus_id)
