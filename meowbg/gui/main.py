import os
import Queue
from kivy.animation import Animation

from kivy.app import App
from kivy.clock import Clock
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
import time
from meowbg.core.board import BLACK, WHITE
from meowbg.core.bot import Bot
from meowbg.core.exceptions import MoveNotPossible
from meowbg.core.match import Match
from meowbg.core.move import PartialMove
from meowbg.core.player import HumanPlayer
from meowbg.gui.basicparts import Spike, SpikePanel, IndexRow, ButtonPanel, BarPanel, BearoffPanel, Checker
from meowbg.gui.boardwidget import BoardWidget
from meowbg.gui.guievents import NewMatchEvent, MoveAttempt, AnimationFinishedEvent, AnimationStartedEvent, HitEvent, PauseEvent
from meowbg.core.events import PlayerStatusEvent, MatchEvent, MoveEvent, SingleMoveEvent, MessageEvent, DiceEvent, CommitEvent
from meowbg.core.messaging import register

resource_add_path(os.path.dirname(__file__) + "/resources")



class MainWidget(GridLayout):

    def __init__(self, **kwargs):
        GridLayout.__init__(self, cols=1, **kwargs)
        accordion = Accordion(orientation='vertical', size_hint=(1, 10))

        self.game_accordion = AccordionItem(title='game')
        self.game_widget = GameWidget()
        self.game_accordion.add_widget(self.game_widget)
        accordion.add_widget(self.game_accordion)

        self.lobby_accordion = AccordionItem(title='network')
        self.lobby_widget = LobbyWidget()
        self.lobby_accordion.add_widget(self.lobby_widget)
        accordion.add_widget(self.lobby_accordion)

        self.add_widget(accordion)


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

        #self.add_widget(Image(source='wood_texture.jpg', pos_hint={'x': 0, 'y': 0},
        #                      allow_stretch=True, keep_ratio=False))
        self.board = BoardWidget(pos_hint={'x': 0, 'y': 0})
        self.add_widget(self.board)
        self.match = None
        self.blocking_events = []
        self.event_queue = Queue.Queue()
        Clock.schedule_interval(self.process_queue, .1)

        # TODO: implement bulk registration
        register(self.handle, NewMatchEvent)
        register(self.handle, MatchEvent)
        register(self.handle, MoveAttempt)
        register(self.handle, DiceEvent)
        register(self.handle, SingleMoveEvent)
        register(self.handle, MoveEvent)
        register(self.handle, CommitEvent)
        register(self.handle, HitEvent)
        register(self.handle, PauseEvent)

        register(self.release, AnimationFinishedEvent)
        register(self.animate_move, AnimationStartedEvent)


    def process_queue(self, dt):
        if not self.event_queue.empty() and not self.blocking_events:
            event = self.event_queue.get()
            Logger.info("============= Processing event %s" % event)
            self._interpret_event(event)
            self.event_queue.task_done()
        elif not self.event_queue.empty():
            Logger.info("Blocking events: %s" % self.blocking_events)

    def handle(self, event):
        if isinstance(event, MoveEvent):
            # A full move event is first split into several single move events
            for m in event.moves:
                self.event_queue.put(SingleMoveEvent(PartialMove(m.origin, m.target)))
                self.event_queue.put(PauseEvent(300))
            return
        elif isinstance(event, SingleMoveEvent):
            self.event_queue.put(PauseEvent(50))

        self.event_queue.put(event)

    def pause(self, pe):
        self.block(pe)
        Clock.schedule_once(lambda e: self.release(pe), pe.ms/1000.0)

    def release(self, release_event):
        Logger.warn("Releasing %s" % release_event)
        self.blocking_events.remove(release_event)

    def block(self, block_event):
        self.blocking_events.append(block_event)

    def execute_move(self, move):
        self.board.move_by_indexes(move.origin, move.target)

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

    def show_dice_roll(self, dice, color):
        self.board.show_dice(dice, color)

    def initialize_new_match(self, match):
        self.match = match
        #self.match.register_player(Bot("Morten", BLACK), BLACK)
        #self.match.register_player(Bot("Hille", WHITE), WHITE)
        #self.match.register_player(HumanPlayer("Johannes", WHITE), WHITE)
        #self.match.register_player(HumanPlayer("Annette", BLACK), BLACK)
        self.match.new_game()

    def attempt_move(self, origin, target):
        try:
            self.match.make_temporary_move(origin, target, self.match.color_to_move_next)
        except MoveNotPossible, msg:
            Logger.error("Not possible: %s" % msg)

    def _interpret_event(self, event):
        if isinstance(event, MatchEvent):
            self.match = event.match
            self.board.synchronize(event.match)
        elif isinstance(event, SingleMoveEvent):
            self.execute_move(event.move)
        elif isinstance(event, DiceEvent):
            self.show_dice_roll(event.dice, event.color)
        elif isinstance(event, NewMatchEvent):
            self.initialize_new_match(event.match)
        elif isinstance(event, CommitEvent):
            self.match.commit()
        elif isinstance(event, MoveAttempt):
            self.attempt_move(event.origin, event.target)
        elif isinstance(event, HitEvent):
            self.board.animate_hit(event.field_idx, event.hitting_color)
        elif isinstance(event, PauseEvent):
            self.pause(event)
        else:
            Logger.error("Cannot interpret event %s" % event)


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


class LobbyWidget(GridLayout):
    def __init__(self, **kwargs):
        kwargs.update({"cols": 1})
        GridLayout.__init__(self, **kwargs)

        self.player_list = PlayerListWidget(size_hint=(1, 15))
        self.add_widget(self.player_list)

        text_input = TextInput(text="invite tigergammon_bot_III",
                               multiline=False,
                               size_hint=(1, 1),
                               on_text_validate=self.send_command)
        self.add_widget(text_input)

    def handle(self, event):
        if isinstance(event, PlayerStatusEvent):
            self.player_list.update_display(event.status_dicts)
        else:
            Logger.error("Cannot handle type %s" % event)

    def send_command(self, cmd):
        self.notify(MessageEvent(cmd))


class BoardApp(App):
    def build(self):
        parent = MainWidget()
        return parent

Factory.register("LobbyWidget", LobbyWidget)
Factory.register("MatchWidget", MatchWidget)
Factory.register("GameWidget", GameWidget)
Factory.register("ButtonPanel", ButtonPanel)
Factory.register("BoardWidget", BoardWidget)
Factory.register("Spike", Spike)
Factory.register("BarPanel", BarPanel)
Factory.register("BearoffPanel", BearoffPanel)
Factory.register("SpikePanel", SpikePanel)
Factory.register("IndexRow", IndexRow)

if __name__ == '__main__':
    app = BoardApp()
    app.run()