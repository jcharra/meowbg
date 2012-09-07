import kivy.resources
from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Rectangle
from kivy.logger import Logger
from kivy.properties import ListProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.core.image import Image
from kivy.uix.widget import Widget
from meowbg.core.board import Board
from meowbg.core.match import Match
from meowbg.network.events import MatchEvent

class Checker(Widget):
    color = ListProperty([1, 1, 1])

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
        c = Checker(size_hint_y=self.CHECKER_PERCENTAGE, pos=next_pos,
            pos_hint={'center_x': 0.5, 'top': top_hint})
        c.color = color
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
        self.listeners = []

    def add_listener(self, listener):
        self.listeners.append(listener)

    def fire_new_game_event(self):
        m = Match()
        m.board = Board()
        m.board.initialize_board()
        e = MatchEvent(m)
        self.notify(e)

    def notify(self, event):
        Logger.info("Notifying %s listeners of event %s, " % (len(self.listeners), event))
        for li in self.listeners:
            li(event)

class DicePanel(FloatLayout):
    def __init__(self, **kwargs):
        FloatLayout.__init__(self, **kwargs)

    def show(self, dice):
        with self.canvas:
            Color(0.9, 0.9, 0.9)
            for idx, die in enumerate(dice):
                die_width = self.height * 0.9
                xstart = self.x + self.width/2.0 - (die_width + 3) * len(dice)/2
                xpos = xstart + (die_width + 3) * idx
                ypos = self.y
                size = die_width, die_width
                Rectangle(source="die%i.png" % die, pos=(xpos, ypos), size=size)
