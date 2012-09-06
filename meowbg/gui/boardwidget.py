from kivy.animation import Animation
from kivy.logger import Logger
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.vector import Vector
from meowbg.gui.basicparts import IndexRow, SpikePanel

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

        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.upper_left_quad = SpikePanel(start_index=12, size_hint=(5/17.5, 5))
        self.add_widget(self.upper_left_quad)
        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.upper_right_quad = SpikePanel(start_index=18, size_hint=(5/17.5, 5))
        self.add_widget(self.upper_right_quad)

        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))

        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(Widget(size_hint=(5/17.5, 1)))
        self.add_widget(Widget(size_hint=(1.5/17.5, 1)))
        self.add_widget(Widget(size_hint=(5/17.5, 1)))

        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))

        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.lower_left_quad = SpikePanel(start_index=11, size_hint=(5/17.5, 5))
        self.add_widget(self.lower_left_quad)
        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.lower_right_quad = SpikePanel(start_index=5, size_hint=(5/17.5, 5))
        self.add_widget(self.lower_right_quad)

        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))
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

        # checker colors
        self.color_map = {1: (.3, .1, 0), 2: (.8, .6, .4)}

        self.spike_for_index = {}
        for s in self.spikes():
            self.spike_for_index[s.board_idx] = s


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

        if self.active_spike is None:
            self.active_spike = spike
            Logger.info("Activated spike with index %s" % self.active_spike.board_idx)
            spike.activated = True
            self.show_possible_moves(spike.board_idx)
        else:
            self.move(self.active_spike, spike, self.release)
            self.active_spike.activated = False
            self.active_spike = None

    def show_possible_moves(self, from_index):
        if not self.match or not self.match.players_remaining_dice:
            return

        dice = self.match.players_remaining_dice
        color = self.match.players_color
        moves = self.match.board.get_possible_moves(dice, color)

        target_indexes = set([m[0].target for m in moves
                              if m[0].origin == from_index])

        Logger.info("Found target indexes %s for origin %s and remaining dice %s" % (target_indexes, from_index, dice))

        for ti in target_indexes:
            spike = self.spike_for_index[ti]
            spike.highlighted = True

    def release(self):
        self.busy = False

    def synchronize(self, match):
        self.match = match
        self.clear_board() # ugly, causes flickering

        on_field = match.board.checkers_on_field

        for idx, checkers in on_field.items():
            amount = len(checkers)
            if amount:
                col = self.color_map[checkers[0]]
                self.add_checkers(idx, col, amount)

    def spikes(self):
        """
        Generator yielding all spikes
        """
        for q in self.quads:
            for s in q.children:
                yield s

    def get_activated_spike(self):
        """
        Returns the first activated spike - assuming there
        exists at most one.
        """
        for s in self.spikes():
            if s.activated:
                return s

    def move(self, spike_origin, spike_target, on_finish):
        """
        Moves a checker from the origin to the target.
        As soon as the animation is finished, the callback
        'on_finish' is called.
        """

        if not spike_origin.children or spike_origin == spike_target:
            return

        topmost = spike_origin.children[0]
        topmost.pos_hint = {} # needed to make animation work ... ?
        target_pos = spike_target.get_next_checker_position()

        def move_finished(e):
            self.transfer_checker(topmost, spike_origin, spike_target)
            if on_finish: on_finish()

        duration = Vector(topmost.pos).distance(target_pos)/1000.0
        animation = Animation(pos=target_pos, duration=duration)
        animation.on_complete = move_finished
        animation.start(topmost)

    def move_by_indexes(self, idx1, idx2, on_finish=None):
        origin, target = map(self._get_spike_by_index, (idx1, idx2))
        self.move(origin, target, on_finish=on_finish)

    def _get_spike_by_index(self, idx):
        # TODO: make "bar" and "off" translate to spikes as well
        quadrant = {0: self.lower_right_quad,
                    1: self.lower_left_quad,
                    2: self.upper_left_quad,
                    3: self.upper_right_quad}
        spike_panel = quadrant[idx/6]
        child_idx = idx % 6 if spike_panel.index_direction == -1 else 5 - idx % 6
        return spike_panel.children[child_idx]

    def transfer_checker(self, checker, origin, target):
        origin.remove_widget(checker)
        target.add_checkers(checker.color, 1)

    def add_checkers(self, field_idx, color, amount=1):
        spike = self._get_spike_by_index(field_idx)
        spike.add_checkers(color, amount)

    def clear_board(self):
        for sp in self.quads:
            for spike in sp.children:
                spike.clear_widgets()

