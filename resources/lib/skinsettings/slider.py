# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from jurialmunkey.ftools import cached_property
from resources.lib.skinsettings.items import PROPERTY_PREFIX, SkinSetting, get_label_text


class SliderAction:
    """Builtin run when its slider step is chosen. Actions without a condition always run."""

    def __init__(self, meta):
        self.meta = meta

    @property
    def action(self):
        return self.meta['action']

    @property
    def condition(self):
        return self.meta.get('condition', '')

    @property
    def is_active(self):
        return not self.condition or xbmc.getCondVisibility(self.condition)

    def run(self):
        # Conditions are checked as each action runs so they see the changes made by earlier actions.
        if not self.is_active:
            return
        # Waiting lets later conditions and the selected step see the changes made by this action.
        xbmc.executebuiltin(self.action, True)


class SliderStep:
    """Slider position with its own label, selected condition and actions."""

    def __init__(self, meta, rank):
        self.meta = meta
        self.rank = rank

    @property
    def label(self):
        return str(self.meta.get('label', ''))

    @property
    def label_text(self):
        return get_label_text(self.label)

    @property
    def is_selected(self):
        return 'selected' in self.meta and xbmc.getCondVisibility(self.meta['selected'])

    @cached_property
    def actions(self):
        return self.get_actions()

    def get_actions(self):
        return [SliderAction(meta) for meta in self.meta.get('onclick', [])]

    def run(self):
        for action in self.actions:
            action.run()


class SliderSetting(SkinSetting):
    """Setting that moves through its steps on a plain slider. The slider positions are the step ranks.

    The selected step is the first step whose selected condition is true, otherwise the last step chosen.
    """

    template = 'slider'
    current_rank = 0

    @cached_property
    def steps(self):
        return self.get_steps()

    def get_steps(self):
        return [SliderStep(meta, rank) for rank, meta in enumerate(self.meta['steps'])]

    @property
    def maximum(self):
        return len(self.steps) - 1

    @property
    def selected_step(self):
        return next((step for step in self.steps if step.is_selected), self.steps[self.current_rank])

    @cached_property
    def label_property(self):
        return f'{PROPERTY_PREFIX}.{self.key}.Label'

    def get_values(self):
        # Template text shows the label of the chosen step with $SUBSTITUTE[steplabel].
        return {**super().get_values(), 'steplabel': f'$INFO[Window.Property({self.label_property})]'}

    def show_step(self, window, step):
        self.current_rank = step.rank
        window.setProperty(self.label_property, step.label_text)

    def set_step(self, window, step):
        window.set_slider_value(self.control_id, step.rank, self.maximum)
        self.show_step(window, step)

    def onrefresh(self, window):
        self.set_step(window, self.selected_step)

    def onclick(self, window):
        # Sliders send a click each time they move.
        step = self.steps[window.get_slider_value(self.control_id)]
        step.run()
        self.show_step(window, step)
