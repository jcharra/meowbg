import os
import Queue
from kivy.animation import Animation

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.factory import Factory
from kivy.logger import Logger
from kivy.resources import resource_add_path
from kivy.vector import Vector
from meowbg.core.board import WHITE
from meowbg.core.exceptions import MoveNotPossible
from meowbg.core.move import PartialMove
from meowbg.gui.basicparts import Spike, SpikePanel, IndexRow, ButtonPanel, BarPanel, BearoffPanel, Checker, Cube
from meowbg.gui.boardwidget import BoardWidget
from meowbg.gui.guievents import (NewMatchEvent, MoveAttemptEvent, AnimationFinishedEvent, AnimationStartedEvent,
                                  HitEvent, PauseEvent, UnhitEvent, MatchFocusEvent, CommitAttemptEvent,
                                  UndoAttemptEvent, RollAttemptEvent, DoubleAttemptEvent)
from meowbg.core.events import PlayerStatusEvent, MatchEvent, MoveEvent, SingleMoveEvent, DiceEvent, CubeEvent, RejectEvent, AcceptEvent, UndoMoveEvent
from meowbg.core.messaging import register, broadcast
from meowbg.network.connectionpool import share_connection
from meowbg.network.telnetconn import TelnetConnection
from meowbg.network.translation import FIBSTranslator

resource_add_path(os.path.dirname(__file__) + "/resources")



class MainWidget(GridLayout):

    def __init__(self, **kwargs):
        GridLayout.__init__(self, cols=1, **kwargs)
        self.accordion = Accordion(orientation='vertical', size_hint=(1, 10))

        self.game_accordion = AccordionItem(title='game')
        self.game_widget = GameWidget()
        self.game_accordion.add_widget(self.game_widget)
        self.accordion.add_widget(self.game_accordion)

        self.lobby_accordion = AccordionItem(title='network')
        self.lobby_widget = NetworkWidget()
        self.lobby_accordion.add_widget(self.lobby_widget)
        self.accordion.add_widget(self.lobby_accordion)

        self.add_widget(self.accordion)
        register(self.focus_game, MatchFocusEvent)

    def focus_game(self, e):
        self.game_accordion.collapse = False
        self.accordion.select(self.game_accordion)


class GameWidget(FloatLayout):
    def __init__(self, **kwargs):
        FloatLayout.__init__(self, **kwargs)

        self.match_widget = MatchWidget(size_hint_y=.9,
            pos_hint={'x': 0, 'y': 0.1})
        button_panel = ButtonPanel(size_hint_y=.1,
            pos_hint={'x': 0, 'y': 0})

        self.add_widget(self.match_widget)
        self.add_widget(button_panel)


class MatchWidget(FloatLayout):
    def __init__(self, **kwargs):
        FloatLayout.__init__(self, **kwargs)

        self.add_widget(Image(source='wood_texture.jpg', pos_hint={'x': 0, 'y': 0},
                              allow_stretch=True, keep_ratio=False))
        self.board = BoardWidget(pos_hint={'x': 0, 'y': 0})
        self.add_widget(self.board)
        self.match = None
        self.represented_color = WHITE

        self.blocking_events = []
        self.event_queue = Queue.Queue()
        Clock.schedule_interval(self.process_queue, .1)

        # Register a lot of events to be queued
        for e in (NewMatchEvent, MatchEvent, MoveAttemptEvent, DiceEvent, SingleMoveEvent,
            MoveEvent, CommitAttemptEvent, UndoAttemptEvent, UndoMoveEvent, HitEvent, UnhitEvent,
            PauseEvent, RollAttemptEvent, DoubleAttemptEvent, AcceptEvent, RejectEvent):
            register(self._insert_into_queue, e)

        register(self.show_cube_challenge, CubeEvent)
        register(self.release, AnimationFinishedEvent)
        register(self.animate_move, AnimationStartedEvent)

    def _insert_into_queue(self, event):
        """
        Basically this just puts the event into the process queue,
        waiting to be dispatched. There may be special treatment
        for certain kinds of events.
        """
        if isinstance(event, MoveEvent):
            # A full move event is first split into several single move events
            for m in event.moves:
                self.event_queue.put(SingleMoveEvent(PartialMove(m.origin, m.target)))
                self.event_queue.put(PauseEvent(300))
            return
        elif isinstance(event, SingleMoveEvent):
            # A single move event is prepended with a tiny
            # pause in order to prevent moving further from a
            # "still empty" field
            self.event_queue.put(PauseEvent(30))

        self.event_queue.put(event)

    def _interpret_event(self, event):
        if isinstance(event, MatchEvent):
            self.match = event.match
            self.board.synchronize(event.match)
            broadcast(MatchFocusEvent())
        elif isinstance(event, SingleMoveEvent):
            self.execute_move(event.move)
        elif isinstance(event, UndoMoveEvent):
            self.execute_undo_move(event.move)
        elif isinstance(event, DiceEvent):
            self.show_dice_roll(event.dice)
        elif isinstance(event, RollAttemptEvent):
            if self.match:
                self.match.roll(self.represented_color)
        elif isinstance(event, CommitAttemptEvent):
            if self.match:
                self.attempt_commit()
        elif isinstance(event, DoubleAttemptEvent):
            if self.match:
                self.match.double(self.represented_color)
        elif isinstance(event, UndoAttemptEvent):
            if self.match:
                self.match.undo(self.represented_color)
        elif isinstance(event, AcceptEvent):
            if self.match:
                self.match.accept_open_offer(event.color)
        elif isinstance(event, MoveAttemptEvent):
            self.attempt_move(event.origin, event.target)
        elif isinstance(event, RejectEvent):
            if self.match:
                self.match.reject_open_offer(event.color)
        elif isinstance(event, HitEvent):
            self.board.animate_hit(event.field_idx, event.hitting_color)
        elif isinstance(event, UnhitEvent):
            self.board.animate_unhit(event.field_idx, event.hit_color)
        elif isinstance(event, PauseEvent):
            self.pause(event)
        else:
            Logger.error("Cannot interpret event %s" % event)

    def process_queue(self, dt):
        if not self.event_queue.empty() and not self.blocking_events:
            event = self.event_queue.get()
            Logger.info("============= Processing event %s" % event)
            self._interpret_event(event)
            self.event_queue.task_done()
        elif not self.event_queue.empty():
            #Logger.info("Blocking events: %s" % self.blocking_events)
            pass

    def pause(self, pe):
        self.block(pe)
        Clock.schedule_once(lambda e: self.release(pe), pe.ms/1000.0)

    def release(self, release_event):
        #Logger.warn("Releasing %s" % release_event)
        self.blocking_events.remove(release_event)

    def block(self, block_event):
        self.blocking_events.append(block_event)

    def execute_move(self, move):
        self.board.move_by_indexes(move.origin, move.target)

    def execute_undo_move(self, move):
        self.board.move_by_indexes(move.origin, move.target, is_undo=True)

    def animate_move(self, ae):
        """
        Interpret an AnimationStartedEvent appropriately
        """
        self.block(ae)
        origin_checker = ae.moving_checker
        target_spike = ae.target_spike
        target_pos = target_spike.get_next_checker_position(origin_checker.model_color)
        size = origin_checker.size
        new_checker = Checker(origin_checker.model_color,
                              size=size, size_hint=(None, None),
                              pos=origin_checker.pos, pos_hint={})
        origin_checker.parent.remove_widget(origin_checker)
        self.add_widget(new_checker)

        def on_finish(e):
            target_spike.add_checker(origin_checker.model_color)
            self.remove_widget(new_checker)
            self.release(ae)

        duration = Vector(origin_checker.pos).distance(target_pos)/(ae.speedup*1000.0)
        animation = Animation(pos=target_pos, duration=duration)
        animation.on_complete = on_finish
        animation.start(new_checker)

    def show_dice_roll(self, dice):
        self.board.show_dice(dice)

    def show_cube_challenge(self, e):
        self.board.cube_challenge(self.match.color_to_move_next, e.cube_number)

    def attempt_move(self, origin, target):
        try:
            self.match.make_temporary_move(origin, target, self.match.color_to_move_next)
        except MoveNotPossible, msg:
            Logger.error("Not possible: %s" % msg)

    def attempt_commit(self):
        try:
            self.match.commit()
        except ValueError, msg:
            Logger.warn(str(msg))


class PlayerListWidget(ScrollView):
    def __init__(self, **kwargs):
        ScrollView.__init__(self, **kwargs)
        self.grid = GridLayout(cols=2, spacing=10,
                               size=(self.width, self.height),
                               size_hint=(None, None))
        self.grid.bind(minimum_height=self.grid.setter('height'))

        self.add_widget(self.grid)

    def update_display(self, status_dicts):
        for item in status_dicts:
            self.grid.add_widget(Label(text=item['name'],
                size=(self.width/2, 25),
                size_hint=(None, None)))
            self.grid.add_widget(Label(text=item['rating'],
                size=(self.width/2, 25),
                size_hint=(None, None)))


class NetworkWidget(GridLayout):
    def __init__(self, **kwargs):
        kwargs.update({"cols": 1})
        GridLayout.__init__(self, **kwargs)

        self.player_list = PlayerListWidget(size_hint=(1, 15))
        self.add_widget(self.player_list)

        connect_button = Button(text="Connect", size_hint=(1, 1))
        connect_button.bind(on_press=self.connect)
        self.add_widget(connect_button)

        self.raw_text_input = TextInput(text="invite expertBotI",
                                        multiline=False,
                                        size_hint=(1, 1))
        self.raw_text_input.bind(on_text_validate=self.send_command)
        self.add_widget(self.raw_text_input)
        self.connection = None

        register(self.handle, PlayerStatusEvent)

    def handle(self, event):
        if isinstance(event, PlayerStatusEvent):
            self.player_list.update_display(event.status_dicts)
        else:
            Logger.error("Cannot handle type %s" % event)

    def connect(self, e):
        if not self.connection:
            self.connection = TelnetConnection("Tigergammon")
            share_connection("Tigergammon", self.connection)

            self.connection.connect(self.handle_input)
            self.parser = FIBSTranslator()
        else:
            Logger.info("Already connected to %s" % self.connection)

    def handle_input(self, data):
        Logger.warn(data)
        events = self.parser.parse_events(data)
        for e in events:
            broadcast(e)

    def send_command(self, *args):
        cmd = self.raw_text_input.text
        if cmd:
            Logger.warn("Sending raw command %s" % cmd)
            self.connection.send(cmd)


class BoardApp(App):
    def build(self):
        parent = MainWidget()
        return parent

Factory.register("LobbyWidget", NetworkWidget)
Factory.register("MatchWidget", MatchWidget)
Factory.register("GameWidget", GameWidget)
Factory.register("ButtonPanel", ButtonPanel)
Factory.register("BoardWidget", BoardWidget)
Factory.register("Spike", Spike)
Factory.register("BarPanel", BarPanel)
Factory.register("BearoffPanel", BearoffPanel)
Factory.register("SpikePanel", SpikePanel)
Factory.register("IndexRow", IndexRow)
Factory.register("Cube", Cube)

if __name__ == '__main__':
    app = BoardApp()
    app.run()