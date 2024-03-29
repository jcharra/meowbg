from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from meowbg.core.board import WHITE, BLACK, BAR_INDEX, OFF_INDEX
from meowbg.core.eventqueue import GlobalTaskQueue
from meowbg.core.events import DiceEvent, CubeEvent
from meowbg.core.messaging import broadcast, register
from meowbg.gui.basicparts import IndexRow, SpikePanel, DicePanel, BarPanel, BearoffPanel, Cube
from meowbg.gui.guievents import MoveAttemptEvent


class BoardWidget(GridLayout):
    def __init__(self, **kwargs):
        kwargs.update({'cols': 7})
        GridLayout.__init__(self, **kwargs)
        self.active_spike = None
        self.match = None

        # plug together all that shit ...
        self.upper_cube_container = BoxLayout(
            size_hint=(1/17.5, 1), orientation='vertical')
        self.add_widget(self.upper_cube_container)
        self.add_widget(IndexRow(idx_start=13, size_hint=(5/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))  # border at bar
        self.add_widget(IndexRow(idx_start=19, size_hint=(5/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))  # border
        self.add_widget(Widget(size_hint=(1/17.5, 1)))  # border above bearoff
        self.add_widget(Widget(size_hint=(1/17.5, 1)))  # border etc. ...

        self.add_widget(Widget(size_hint=(1/17.5, 5)))
        self.upper_left_quad = SpikePanel(
            start_index=12, size_hint=(5/17.5, 5))
        self.add_widget(self.upper_left_quad)
        self.upper_bar = BarPanel(size_hint=(1/17.5, 5), direction=1)
        self.add_widget(self.upper_bar)
        self.upper_right_quad = SpikePanel(
            start_index=18, size_hint=(5/17.5, 5))
        self.add_widget(self.upper_right_quad)

        self.add_widget(Widget(size_hint=(1/17.5, 5)))
        self.upper_bearoff = BearoffPanel(size_hint=(1/17.5, 5))
        self.add_widget(self.upper_bearoff)
        self.add_widget(Widget(size_hint=(1/17.5, 5)))

        self.middle_cube_container = BoxLayout(
            size_hint=(1/17.5, 1), orientation='vertical')
        self.add_widget(self.middle_cube_container)
        self.blacks_dice_area = DicePanel(size_hint=(5/17.5, 1))
        self.add_widget(self.blacks_dice_area)
        self.cube_challenge_container = BoxLayout(
            size_hint=(1.5/17.5, 1), orientation='vertical')
        self.add_widget(self.cube_challenge_container)
        self.whites_dice_area = DicePanel(size_hint=(5/17.5, 1))
        self.add_widget(self.whites_dice_area)

        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))

        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.lower_left_quad = SpikePanel(
            start_index=11, size_hint=(5/17.5, 5))
        self.add_widget(self.lower_left_quad)

        self.lower_bar = BarPanel(size_hint=(1/17.5, 5), direction=-1)
        self.add_widget(self.lower_bar)

        self.lower_right_quad = SpikePanel(
            start_index=5, size_hint=(5/17.5, 5))
        self.add_widget(self.lower_right_quad)

        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.lower_bearoff = BearoffPanel(size_hint=(1/17.5, 5))
        self.add_widget(self.lower_bearoff)
        self.add_widget(Widget(size_hint=(1/17.5, 1)))

        self.lower_cube_container = BoxLayout(
            size_hint=(1/17.5, 1), orientation='vertical')
        self.add_widget(self.lower_cube_container)
        self.add_widget(
            IndexRow(idx_start=12, idx_direction=-1, size_hint=(5/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(
            IndexRow(idx_start=6, idx_direction=-1, size_hint=(5/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))
        self.add_widget(Widget(size_hint=(1/17.5, 1)))

        self.quads = (self.upper_left_quad, self.upper_right_quad,
                      self.lower_left_quad, self.lower_right_quad)

        self.upper_bar.board_idx = self.upper_bearoff.board_idx = 24
        self.lower_bar.board_idx = self.lower_bearoff.board_idx = -1

        # Mapping from spikes to indexes - not including the bars
        self.spike_for_target_index = {}
        for s in self.spikes():
            self.spike_for_target_index[s.board_idx] = s

        self.cube = Cube()
        self.middle_cube_container.add_widget(self.cube)

        sync_call = GlobalTaskQueue.synced_call
        register(sync_call(self.on_dice_event), DiceEvent)
        register(sync_call(self.cube_challenge), CubeEvent)

    def on_touch_down(self, touch):
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
                broadcast(MoveAttemptEvent(spike.board_idx, target_indexes[0]))
            elif len(target_indexes) > 0:
                # highlight clicked spike and show possibilities
                self.active_spike = spike
                spike.activated = True
                self.highlight_possible_targets(target_indexes)
            else:
                Logger.info("No possible moves from %s" % spike.board_idx)
        else:
            broadcast(MoveAttemptEvent(
                self.active_spike.board_idx, spike.board_idx))
            self.active_spike.activated = False
            self.active_spike = None

    def highlight_possible_targets(self, target_indexes):
        for ti in target_indexes:
            spike = self.spike_for_target_index[ti]
            spike.highlighted = True

    def synchronize(self, match):
        """
        Update display according to what's in the given match
        """
        self.match = match
        # Logger.info("Sync with %s" % self.match)

        self.clear_board()

        on_field = match.board.checkers_on_field

        for idx, checkers in on_field.items():
            amount = len(checkers)
            if amount:
                col = checkers[0]
                self.add_checkers(idx, col, amount)

        on_bar = match.board.checkers_on_bar
        for col, target in ((WHITE, self.lower_bar), (BLACK, self.upper_bar)):
            col_on_bar = on_bar.count(col)
            if col_on_bar:
                target.add_checkers(col, col_on_bar)

        borne_off = match.board.borne_off
        for col, target in ((WHITE, self.upper_bearoff), (BLACK, self.lower_bearoff)):
            col_borne_off = borne_off.count(col)
            if col_borne_off:
                target.add_checkers(col, col_borne_off)

        dice = self.match.remaining_dice
        self.show_dice(dice)

        if not match.open_cube_challenge_from_color:
            self.set_cube_to_owning_color()

    def set_cube_to_owning_color(self):
        if self.match.may_double[WHITE] and not self.match.may_double[BLACK]:
            target = self.upper_cube_container
        elif self.match.may_double[BLACK] and not self.match.may_double[WHITE]:
            target = self.lower_cube_container
        else:
            target = self.middle_cube_container
        self.set_cube(target, self.match.cube)

    def move_cube(self, target_pos):
        # TODO
        pass

    def set_cube(self, target, cube):
        if self.cube.parent:
            self.cube.parent.remove_widget(self.cube)
        target.add_widget(self.cube)
        self.cube.set_number(cube)

    def cube_challenge(self, cube_event, on_finish):
        self.set_cube(self.cube_challenge_container, cube_event.cube_number)
        on_finish()

    def on_dice_event(self, dice_event, on_finish):
        dice = dice_event.dice
        self.show_dice(dice)
        on_finish()

    def show_dice(self, dice):
        self.blacks_dice_area.clear_widgets()
        self.whites_dice_area.clear_widgets()

        if not dice:
            return

        color = self.match.color_to_move_next
        if color == BLACK:
            self.blacks_dice_area.show_dice(dice)
        else:
            self.whites_dice_area.show_dice(dice)

    def spikes(self):
        """
        Helper function to get all spikes, including both bars and bearoffs
        """
        s = [self.lower_bar, self.upper_bar,
             self.lower_bearoff, self.upper_bearoff]
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

    def get_animation_data(self, origin_idx, target_idx):
        origin_spike, target_spike = self.get_spikes_for_move_indexes(
            origin_idx, target_idx)
        moving_checker = origin_spike.children[0]
        return moving_checker, target_spike

    def get_undo_animation_data(self, origin_idx, target_idx):
        origin_spike, target_spike = self.get_spikes_for_move_indexes(origin_idx=target_idx,
                                                                      target_idx=origin_idx,
                                                                      is_undo=True)
        moving_checker = origin_spike.children[0]
        return moving_checker, target_spike

    def get_hit_animation_data(self, target_idx):
        target_spike = self._get_spike_by_index(target_idx)
        hit_checker = target_spike.children[0]
        bar = self.upper_bar if hit_checker.model_color == BLACK else self.lower_bar
        return hit_checker, bar

    def get_bar_checker(self, hit_color):
        bar = self.upper_bar if hit_color == BLACK else self.lower_bar
        if bar.children:
            return bar.children[0]
        Logger.error("There's no checker of color %s at bar" % hit_color)

    def get_spikes_for_move_indexes(self, origin_idx, target_idx, is_undo=False):
        """
        Returns the spikes corresponding to the given move's indexes.
        The parameter `is_undo` indicates whether this is a backwards
        move, i.e. a previous move being undone.
        """
        move_direction = target_idx - origin_idx
        origin = target = None

        if origin_idx in BAR_INDEX.values():
            if move_direction > 0:
                if is_undo:
                    origin = self.lower_bearoff
                else:
                    origin = self.lower_bar
            else:
                if is_undo:
                    origin = self.upper_bearoff
                else:
                    origin = self.upper_bar
        elif target_idx in OFF_INDEX.values():
            if move_direction > 0:
                if is_undo:
                    target = self.upper_bar
                else:
                    target = self.upper_bearoff
            else:
                if is_undo:
                    target = self.lower_bar
                else:
                    target = self.lower_bearoff

        origin = origin or self._get_spike_by_index(origin_idx)
        target = target or self._get_spike_by_index(target_idx)

        return origin, target

    def clear_board(self):
        for spike in self.spikes():
            spike.clear_widgets()

    def _get_spike_by_index(self, idx):
        quadrant = {0: self.lower_right_quad,
                    1: self.lower_left_quad,
                    2: self.upper_left_quad,
                    3: self.upper_right_quad}
        spike_panel = quadrant[idx//6]
        child_idx = idx % 6 if spike_panel.index_direction == -1 else 5 - idx % 6
        return spike_panel.children[child_idx]

    def add_checkers(self, field_idx, color, amount=1):
        spike = self._get_spike_by_index(field_idx)
        spike.add_checkers(color, amount)
