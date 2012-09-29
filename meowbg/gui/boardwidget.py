from kivy.animation import Animation
from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Rectangle
from kivy.logger import Logger
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.vector import Vector
from meowbg.core.board import WHITE, BLACK, BAR_INDEX, OFF_INDEX
from meowbg.core.match import Match
from meowbg.core.messaging import broadcast
from meowbg.core.move import PartialMove
from meowbg.gui.basicparts import IndexRow, SpikePanel, DicePanel, BarPanel, BearoffPanel
from meowbg.gui.guievents import MoveAttempt, AnimationFinishedEvent, AnimationStartedEvent, HitEvent


class BoardWidget(GridLayout):
    def __init__(self, **kwargs):
        kwargs.update({'cols': 7})
        GridLayout.__init__(self, **kwargs)
        self.active_spike = None
        self.busy = False
        self.match = None

        # plug together all that shit ...
        self.add_widget(Widget(size_hint=(1/17.5, 1))) # border
        self.add_widget(IndexRow(idx_start=13, size_hint=(5/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1))) # border at bar
        self.add_widget(IndexRow(idx_start=19, size_hint=(5/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1))) # border
        self.add_widget(Widget(size_hint=(1/17.5, 1))) # border above bearoff
        self.add_widget(Widget(size_hint=(1/17.5, 1))) # border etc. ... 

        self.add_widget(Widget(size_hint=(1/17.5, 5)))
        self.upper_left_quad = SpikePanel(start_index=12, size_hint=(5/17.5, 5))
        self.add_widget(self.upper_left_quad)
        self.upper_bar = BarPanel(size_hint=(1/17.5, 5))
        self.add_widget(self.upper_bar)
        self.upper_right_quad = SpikePanel(start_index=18, size_hint=(5/17.5, 5))
        self.add_widget(self.upper_right_quad)

        self.add_widget(Widget(size_hint=(1/17.5, 5)))
        self.upper_bearoff = BearoffPanel(size_hint=(1/17.5, 5))
        self.add_widget(self.upper_bearoff)
        self.add_widget(Widget(size_hint=(1/17.5, 5)))

        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.opponents_dice_area = DicePanel(size_hint=(5/17.5, 1))
        self.add_widget(self.opponents_dice_area)
        self.add_widget(Widget(size_hint=(1.5/17.5, 1)))
        self.players_dice_area = DicePanel(size_hint=(5/17.5, 1))
        self.add_widget(self.players_dice_area)

        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))

        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.lower_left_quad = SpikePanel(start_index=11, size_hint=(5/17.5, 5))
        self.add_widget(self.lower_left_quad)

        self.lower_bar = BarPanel(size_hint=(1/17.5, 5))
        self.add_widget(self.lower_bar)

        self.lower_right_quad = SpikePanel(start_index=5, size_hint=(5/17.5, 5))
        self.add_widget(self.lower_right_quad)

        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.lower_bearoff = BearoffPanel(size_hint=(1/17.5, 5))
        self.add_widget(self.lower_bearoff)
        self.add_widget(Widget(size_hint=(1/17.5, 1)))

        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(IndexRow(idx_start=12, idx_direction=-1, size_hint=(5/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(IndexRow(idx_start=6, idx_direction=-1, size_hint=(5/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))

        self.quads = (self.upper_left_quad, self.upper_right_quad,
                      self.lower_left_quad, self.lower_right_quad)

        self.lower_bar.board_idx = self.lower_bearoff.board_idx = 24
        self.upper_bar.board_idx = self.upper_bearoff.board_idx = -1

        # Mapping from spikes to indexes - not including the bars
        self.spike_for_target_index = {}
        for s in self.spikes():
            self.spike_for_target_index[s.board_idx] = s

    def on_touch_down(self, touch):
        if self.busy:
            return

        for s in self.spikes():
            if s.collide_point(*touch.pos):
                self.activate_spike(s)
                break

    def deactivate_all_spikes(self):
        for s in self.spikes():
            s.activated = s.highlighted = False

    def activate_spike(self, spike):
        self.deactivate_all_spikes()
        if not self.match:
            return

        if self.active_spike is None:
            moves = self.match.board.get_remaining_possible_moves()
            target_indexes = list(set([m[0].target for m in moves
                                       if m[0].origin == spike.board_idx]))

            if len(target_indexes) == 1:
                # only one possibility => move immediately
                broadcast(MoveAttempt(spike.board_idx, target_indexes[0]))
            else:
                # highlight clicked spike and show possibilities
                self.active_spike = spike
                spike.activated = True
                self.highlight_possible_targets(target_indexes)
        else:
            broadcast(MoveAttempt(self.active_spike.board_idx, spike.board_idx))
            self.active_spike.activated = False
            self.active_spike = None

    def highlight_possible_targets(self, target_indexes):
        for ti in target_indexes:
            spike = self.spike_for_target_index[ti]
            spike.highlighted = True

    def release(self):
        self.busy = False

    def synchronize(self, match):
        self.match = match
        Logger.info("Sync with %s" % self.match)

        self.clear_board() # ugly, causes flickering

        on_field = match.board.checkers_on_field

        for idx, checkers in on_field.items():
            amount = len(checkers)
            if amount:
                col = checkers[0]
                self.add_checkers(idx, col, amount)

    def show_dice(self, dice, color):
        self.opponents_dice_area.clear_widgets()
        self.players_dice_area.clear_widgets()

        if color == BLACK:
            self.opponents_dice_area.show_dice(dice)
        else:
            self.players_dice_area.show_dice(dice)

    def spikes(self):
        """
        Helper function to get all spikes, including both bars and bearoffs
        """
        s = [self.lower_bar, self.upper_bar, self.lower_bearoff, self.upper_bearoff]
        for q in self.quads:
            s.extend(q.children)
        return s

    def get_activated_spike(self):
        """
        Returns the first activated spike - assuming there
        exists at most one.
        """
        for s in self.spikes():
            if s.activated:
                return s

    def move(self, spike_origin, spike_target):
        if not spike_origin.children:
            raise ValueError("method 'move' called with empty origin")

        moving_checker = spike_origin.children[0]
        self.move_checker(moving_checker, spike_origin, spike_target)

    def move_checker(self, moving_checker, spike_origin, spike_target):
        """
        Moves a checker from the origin to the target.
        """
        moving_checker.pos_hint = {} # needed to make animation work ... ?
        target_pos = spike_target.get_next_checker_position()

        def move_finished(e):
            self.transfer_checker(moving_checker, spike_origin, spike_target)
            broadcast(AnimationFinishedEvent(moving_checker))

        duration = Vector(moving_checker.pos).distance(target_pos)/1000.0
        animation = Animation(pos=target_pos, duration=duration)
        animation.on_complete = move_finished

        broadcast(AnimationStartedEvent(moving_checker))
        animation.start(moving_checker)

    def move_by_indexes(self, origin_idx, target_idx):
        """
        Performs a move from origin index to target index, potentially
        hitting a checker on the target field.
        """
        move_direction = target_idx - origin_idx
        origin = target = None

        if origin_idx in BAR_INDEX.values():
            origin = self.upper_bar if move_direction > 0 else self.lower_bar
        elif target_idx in OFF_INDEX.values():
            target = self.upper_bearoff if move_direction < 0 else self.lower_bearoff

        origin = origin or self._get_spike_by_index(origin_idx)
        target = target or self._get_spike_by_index(target_idx)

        self.move(origin, target)

    def _get_spike_by_index(self, idx):
        quadrant = {0: self.lower_right_quad,
                    1: self.lower_left_quad,
                    2: self.upper_left_quad,
                    3: self.upper_right_quad}
        spike_panel = quadrant[idx/6]
        child_idx = idx % 6 if spike_panel.index_direction == -1 else 5 - idx % 6
        return spike_panel.children[child_idx]

    def transfer_checker(self, checker, origin, target):
        origin.remove_widget(checker)
        target.add_checkers(checker.model_color, 1)

    def add_checkers(self, field_idx, color, amount=1):
        spike = self._get_spike_by_index(field_idx)
        spike.add_checkers(color, amount)

    def animate_hit(self, field_idx, hitting_color):
        spike = self._get_spike_by_index(field_idx)
        for c in spike.children:
            if c.model_color != hitting_color:
                target = self.lower_bar if c.model_color == BLACK else self.upper_bar
                self.move_checker(c, spike, target)
                return
        raise ValueError("No conflicting colors for %s on spike %s: %s"
                         % (hitting_color, spike, [c.model_color for c in spike.children]))

    def clear_board(self):
        for sp in self.quads:
            for spike in sp.children:
                spike.clear_widgets()

