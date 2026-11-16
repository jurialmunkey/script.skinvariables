# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
from jurialmunkey.ftools import cached_property
from resources.lib.skinsettings.commands import BuiltinAction, get_setting_action
from resources.lib.skinsettings.items import PROPERTY_PREFIX, SkinSetting, get_label_text


class SliderStep:
    """Slider position with its own label, selected condition and builtins.

    Sliders click on every move so steps only run builtins and not $COMMAND actions.
    """

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
        return [BuiltinAction(meta) for meta in self.meta.get('onclick', [])]

    def run(self, window, setting):
        for action in self.actions:
            action.run(window, setting)


class SliderSetting(SkinSetting):
    """Setting that moves through its steps on a plain slider. The slider positions are the step ranks.

    The selected step is the first step whose selected condition is true, otherwise the last step chosen.
    Onunclick actions run when select is pressed on the slider and can include $COMMAND actions.
    """

    template = 'slider'
    current_rank = 0

    @cached_property
    def steps(self):
        return self.get_steps()

    def get_steps(self):
        return [SliderStep(meta, rank) for rank, meta in enumerate(self.meta['steps'])]

    @cached_property
    def onunclick_actions(self):
        return self.get_onunclick_actions()

    def get_onunclick_actions(self):
        return [get_setting_action(meta) for meta in self.meta.get('onunclick', [])]

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
        step.run(window, self)
        self.show_step(window, step)

    def onselect(self, window):
        # Kodi sliders do not click when select is pressed so the window passes the select action instead.
        for action in self.onunclick_actions:
            action.run(window, self)
