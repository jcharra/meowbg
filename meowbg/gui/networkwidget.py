
from meowbg.core.messaging import register, broadcast
from meowbg.network.connectionpool import share_connection
from meowbg.network.telnetconn import TelnetConnection
from meowbg.network.translation import FIBSTranslator
from meowbg.core.events import PlayerStatusEvent, GlobalShutdownEvent

from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.logger import Logger


class PlayerListWidget(ScrollView):
    def __init__(self, **kwargs):
        ScrollView.__init__(self, **kwargs)
        self.grid = GridLayout(cols=1, spacing=10,
                               size=(self.width, self.height),
                               size_hint=(None, None))
        self.grid.bind(minimum_height=self.grid.setter('height'))

        self.add_widget(self.grid)

    def update_display(self, status_dicts):
        for item in status_dicts:
            self.grid.add_widget(PlayerRow(size=(self.width, 25),
                                           size_hint=(None, None),
                                           player_info=item))


class PlayerRow(BoxLayout):
    def __init__(self, *args, **kwargs):
        BoxLayout.__init__(self, *args, **kwargs)
        self.player_info = kwargs.get("player_info")

        self.add_widget(Label(text=self.player_info["name"]))
        self.add_widget(Label(text=self.player_info["rating"]))
        self.add_widget(Label(text=self.player_info["experience"]))
        self.add_widget(Label(text=self.player_info["client"]))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            Logger.info("Clicked me! I'm player %s" % self.player_info["name"])


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
        register(self.tear_down, GlobalShutdownEvent)

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

    def tear_down(self, e):
        Logger.warn("Network shutdown")
        if self.connection:
            self.connection.shutdown()

    def handle_input(self, data):
        Logger.warn(data)
        events = self.parser.parse_events(data)
        for e in events:
            broadcast(e)

    def send_command(self, *args):
        cmd = self.raw_text_input.text
        if cmd and self.connection:
            Logger.warn("Sending raw command %s" % cmd)
            self.connection.send(cmd)


