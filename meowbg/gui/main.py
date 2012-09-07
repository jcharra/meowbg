import os
import Queue
from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics.vertex_instructions import Rectangle
from kivy.properties import ObjectProperty
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.factory import Factory
from kivy.logger import Logger
from kivy.resources import resource_add_path
from meowbg.core.move import PartialMove
from meowbg.gui.basicparts import Spike, SpikePanel, IndexRow, ButtonPanel
from meowbg.gui.boardwidget import BoardWidget
from meowbg.network.bot import Bot
from meowbg.network.eventhandlers import FIBSEventHandler, AIEventHandler
from meowbg.network.events import PlayerStatusEvent, MatchEvent, MoveEvent, SingleMoveEvent, MessageEvent, DiceEvent

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

        #self.game_event_handler = FIBSEventHandler(TelnetClient())
        self.game_event_handler = AIEventHandler(Bot())

        # 'Incoming' events from the game event handler are dealt with
        # by an instance method for further distribution.
        self.game_event_handler.add_listener(self.notify_external_event)
        self.game_event_handler.connect()

        # 'Outgoing' events from the game widget need to be propagated
        # to the game event handler. They may originate from the game
        # or lobby widget.
        self.game_widget.add_listener(self.game_event_handler.handle)
        self.lobby_widget.add_listener(self.game_event_handler.handle)

    def notify_external_event(self, event):
        """
        Notification about meowbg (non-kivy) events coming from external,
        i.e. from the game event handler.
        """
        Logger.info("Received event %s" % event)

        if isinstance(event, PlayerStatusEvent):
            self.lobby_widget.handle(event)
        elif isinstance(event, (MatchEvent, MoveEvent, DiceEvent)):
            self.game_widget.handle(event)
        else:
            Logger.error("Cannot handle type %s" % event)


class GameWidget(GridLayout):
    def __init__(self, **kwargs):
        GridLayout.__init__(self, orientation='vertical', cols=1, **kwargs)

        self.match_widget = MatchWidget(size_hint=(1, 10))
        button_panel = ButtonPanel(size_hint=(1, 1))

        self.add_widget(self.match_widget)
        self.add_widget(button_panel)

        self.match_widget.add_listener(self.notify)
        button_panel.add_listener(self.notify)

        self.listeners = []

    def add_listener(self, listener):
        self.listeners.append(listener)

    def notify(self, event):
        for li in self.listeners:
            li(event)

    def handle(self, event):
        if isinstance(event, (MatchEvent, MoveEvent, DiceEvent)):
            self.match_widget.handle(event)
        else:
            raise Logger.error("Cannot handle type %s" % event)

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

        self.listeners = []

    def handle(self, event):
        if isinstance(event, PlayerStatusEvent):
            self.player_list.update_display(event.status_dicts)
        else:
            Logger.error("Cannot handle type %s" % event)

    def add_listener(self, listener):
        self.listeners.append(listener)

    def notify(self, event):
        Logger.debug("Notifying %s listeners of event %s" % (len(self.listeners), event))
        for li in self.listeners:
            li(event)

    def send_command(self, cmd):
        self.notify(MessageEvent(cmd))

class MatchWidget(FloatLayout):
    board = ObjectProperty(None)

    def __init__(self, **kwargs):
        FloatLayout.__init__(self, **kwargs)

        self.listeners = []

        self.busy = False
        self.event_queue = Queue.Queue()
        Clock.schedule_interval(self.process_queue, 0.1)

    def process_queue(self, dt):
        if not self.event_queue.empty() and not self.busy:
            event = self.event_queue.get()
            Logger.info("Processing event %s" % event)
            self._interpret_event(event)
            self.event_queue.task_done()

    def add_listener(self, listener):
        self.listeners.append(listener)

    def notify(self, event):
        Logger.info("Event %s fired" % event)
        for s in self.listeners:
            s(event)

    def handle(self, event):
        self.event_queue.put(event)

    def release(self):
        self.busy = False

    def execute_move(self, move):
        self.busy = True
        self.board.move_by_indexes(move.origin, move.target, self.release)

    def show_dice_roll(self, dice, color):
        self.busy = True
        self.board.show_dice(dice, color, self.release)

    def _interpret_event(self, event):
        if isinstance(event, MatchEvent):
            self.board.synchronize(event.match)
        elif isinstance(event, MoveEvent):
            # A full move event is split into several single move events
            for m in event.moves:
                self.event_queue.put(SingleMoveEvent(PartialMove(m.origin, m.target)))
        elif isinstance(event, SingleMoveEvent):
            self.execute_move(event.move)
        elif isinstance(event, DiceEvent):
            self.show_dice_roll(event.dice, event.color)
        else:
            Logger.error("Cannot interpret event %s" % event)

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