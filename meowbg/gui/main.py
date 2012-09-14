import os
import Queue

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.factory import Factory
from kivy.logger import Logger
from kivy.resources import resource_add_path
from meowbg.core.board import BLACK, WHITE
from meowbg.core.exceptions import MoveNotPossible
from meowbg.core.match import Match
from meowbg.core.move import PartialMove
from meowbg.gui.basicparts import Spike, SpikePanel, IndexRow, ButtonPanel
from meowbg.gui.boardwidget import BoardWidget
from meowbg.gui.guievents import NewMatchEvent, MoveAttempt, AnimationFinishedEvent
from meowbg.network.bot import Bot
from meowbg.network.eventhandlers import  AIEventHandler
from meowbg.core.events import PlayerStatusEvent, MatchEvent, MoveEvent, SingleMoveEvent, MessageEvent, DiceEvent, CommitEvent
from meowbg.core.messaging import register, broadcast

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

        self.game_event_handler = AIEventHandler(Bot(BLACK))


class GameWidget(GridLayout):
    def __init__(self, **kwargs):
        GridLayout.__init__(self, orientation='vertical', cols=1, **kwargs)

        self.match_widget = MatchWidget(size_hint=(1, 10))
        button_panel = ButtonPanel(size_hint=(1, 1))

        self.add_widget(self.match_widget)
        self.add_widget(button_panel)


class MatchWidget(GridLayout):

    def __init__(self, **kwargs):
        kwargs.update({"cols": 1})
        GridLayout.__init__(self, **kwargs)

        #self.add_widget(Image(source='wood_texture.jpg', pos=(self.x, self.y),
        #                      allow_stretch=True, keep_ratio=False))
        self.board = BoardWidget(pos=(self.x, self.y))
        self.add_widget(self.board)
        self.match = None
        self.blocking_event = None
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
        register(self.release, AnimationFinishedEvent)

    def process_queue(self, dt):
        if not self.event_queue.empty() and not self.blocking_event:
            event = self.event_queue.get()
            Logger.info("Processing event %s" % event)
            self._interpret_event(event)
            self.event_queue.task_done()
        #else:
        #    Logger.info("Empty: %s Blocking event: %s" % (self.event_queue.empty(), self.blocking_event))

    def handle(self, event):
        if isinstance(event, MoveEvent):
            # A full move event is first split into several single move events
            for m in event.moves:
                self.event_queue.put(SingleMoveEvent(PartialMove(m.origin, m.target)))
        else:
            self.event_queue.put(event)

    def release(self, e):
        self.blocking_event = None

    def execute_move(self, move):
        self.blocking_event = move
        self.board.move_by_indexes(move.origin, move.target)

    def show_dice_roll(self, dice, color):
        self.blocking_event = "diceroll"
        self.board.show_dice(dice, color)

    def initialize_new_match(self, length):
        self.match = Match()
        self.match.length = length
        self.match.player_names[WHITE] = "Player"
        self.match.player_names[BLACK] = "Bot"
        self.match.new_game()

    def attempt_move(self, origin, target):
        try:
            self.match.make_temporary_move(origin, target, self.match.turn)
        except MoveNotPossible, msg:
            Logger.error("Not possible: %s" % msg)

    def _interpret_event(self, event):
        if isinstance(event, MatchEvent):
            self.board.synchronize(event.match)
        elif isinstance(event, SingleMoveEvent):
            self.execute_move(event.move)
        elif isinstance(event, DiceEvent):
            self.show_dice_roll(event.dice, event.color)
        elif isinstance(event, NewMatchEvent):
            self.initialize_new_match(event.length)
        elif isinstance(event, CommitEvent):
            # XXX: Commit event may have color None => default to player's color :(
            self.match.commit(event.color or WHITE)
        elif isinstance(event, MoveAttempt):
            self.attempt_move(event.origin, event.target)
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
Factory.register("SpikePanel", SpikePanel)
Factory.register("IndexRow", IndexRow)

if __name__ == '__main__':
    app = BoardApp()
    app.run()