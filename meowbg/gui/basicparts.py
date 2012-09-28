from kivy.logger import Logger
from kivy.properties import ListProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from meowbg.core.board import WHITE, BLACK
from meowbg.core.match import Match
from meowbg.core.events import MatchEvent, CommitEvent
from meowbg.core.messaging import broadcast
from meowbg.gui.guievents import NewMatchEvent

class Checker(Widget):
    COLOR_MAP = {WHITE: (.3, .1, 0), BLACK: (.8, .6, .4)}

    def __init__(self, model_color, **kwargs):
        self.model_color = model_color
        self.color = self.COLOR_MAP[model_color]
        Widget.__init__(self, **kwargs)

class IndexRow(BoxLayout):
    idx_start = NumericProperty(0)
    idx_direction = NumericProperty(1)

class Spike(FloatLayout):
    CHECKER_PERCENTAGE = 0.19
    activated = BooleanProperty(False)
    highlighted = BooleanProperty(False)
    board_idx = NumericProperty(0)

    def __init__(self, **kwargs):
        FloatLayout.__init__(self, **kwargs)
        self.direction = kwargs.get('direction', 1)

    def add_checkers(self, color, amount):
        for _ in range(amount):
            self.add_checker(color)

    def add_checker(self, color):
        next_pos = self.get_next_checker_position()
        if self.direction == 1:
            top_hint = self.CHECKER_PERCENTAGE * (self._get_y_displacement(len(self.children)) + 1)
        else:
            top_hint = 1 - self.CHECKER_PERCENTAGE * self._get_y_displacement(len(self.children))
        c = Checker(color, size_hint_y=self.CHECKER_PERCENTAGE, pos=next_pos,
            pos_hint={'center_x': 0.5, 'top': top_hint})
        self.add_widget(c)

    def _get_y_displacement(self, num):
        """
        For a number in range 0..14 (i.e. amount of checkers
        on this spike) get the 'units' (checker height) by which the next
        checker is to be moved in vertical direction, to achieve stacking
        of all checkers in a 5-4-3-2-1 scheme.
        """
        if num < 5:
            return num
        elif num < 9:
            return (num % 5) + 0.5
        elif num < 12:
            return (num % 9) + 1
        elif num < 14:
            return (num % 12) + 1.5
        else:
            return 2

    def get_next_checker_position(self):
        """
        Returns the target position for an additional checker
        """
        num_children = len(self.children)
        checker_height = self.height * self.CHECKER_PERCENTAGE

        if not num_children:
            pos_y = 0 if self.direction == 1 else self.height * 0.8
        else:
            if self.direction == 1:
                pos_y = checker_height * self._get_y_displacement(num_children)
            else:
                pos_y = self.height - checker_height * (self._get_y_displacement(num_children) + 1)

        return self.pos[0], self.pos[1] + pos_y

    def has_different_coloured_checker(self, hitting_checkers_color):
        """
        Checks whether there is a checker of a color different
        from the given color at index 0.
        """
        for c in self.children:
            if c.model_color != hitting_checkers_color:
                Logger.warn("Found enemy checker with color %s != %s" %
                            (c.model_color, hitting_checkers_color))
                return True
        return False


class SpikePanel(BoxLayout):
    def __init__(self, start_index, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        self.index_direction = 1 if start_index > 11 else -1
        for i in range(6):
            self.add_widget(Spike(board_idx=start_index + i * self.index_direction,
                                  direction=-self.index_direction))

class ButtonPanel(BoxLayout):
    def __init__(self, **kwargs):
        BoxLayout.__init__(self, **kwargs)

    def fire_new_game_event(self):
        broadcast(NewMatchEvent(1))

    def commit_move(self):
        broadcast(CommitEvent())

class DicePanel(GridLayout):
    def __init__(self, **kwargs):
        kwargs.update({'cols': 8})
        GridLayout.__init__(self, **kwargs)

    def show_dice(self, dice):
        self.add_widget(Widget(size_hint=(4-len(dice)/2, 1))) # spacer
        for idx, die in enumerate(dice):
            self.add_widget(Image(source="die%i.png" % die))
        self.add_widget(Widget(size_hint=(4-len(dice)/2, 1))) # spacer

class BarPanel(Spike):
    def __init__(self, **kwargs):
        kwargs.update({'cols': 1})
        Spike.__init__(self, **kwargs)

class BearoffPanel(Spike):
    def __init__(self, **kwargs):
        kwargs.update({'cols': 1})
        Spike.__init__(self, **kwargs)
