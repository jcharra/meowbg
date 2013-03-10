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
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.factory import Factory
from kivy.logger import Logger
from kivy.resources import resource_add_path
from kivy.vector import Vector
from meowbg.core.board import WHITE, BLACK
from meowbg.core.exceptions import MoveNotPossible
from meowbg.gui.basicparts import Spike, SpikePanel, IndexRow, ButtonPanel, BarPanel, BearoffPanel, Checker, Cube
from meowbg.gui.boardwidget import BoardWidget
from meowbg.gui.guievents import (MoveAttemptEvent, AnimationStartedEvent, PauseEvent, MatchFocusEvent, CommitAttemptEvent,
                                  UndoAttemptEvent, RollAttemptEvent, DoubleAttemptEvent, ResignAttemptEvent)
from meowbg.core.events import (PlayerStatusEvent, MatchEvent, SingleMoveEvent, RejectEvent, AcceptEvent, UndoMoveEvent,
                                MatchEndEvent, GameEndEvent, JoinChallengeEvent, ResignOfferEvent, GlobalShutdownEvent,
                                AcceptJoinEvent)
from meowbg.core.messaging import register, broadcast
from meowbg.gui.popups import OKDialog, ResignDialog, BetweenGamesDialog
from meowbg.network.connectionpool import share_connection
from meowbg.network.telnetconn import TelnetConnection
from meowbg.network.translation import FIBSTranslator
from meowbg.core.eventqueue import GlobalTaskQueue

resource_add_path(os.path.dirname(__file__) + "/resources")


class MainWidget(GridLayout):

    def __init__(self, **kwargs):
        GridLayout.__init__(self, cols=1, **kwargs)
        self.accordion = Accordion(orientation='vertical', size_hint=(1, 10))

        self.game_accordion = AccordionItem(title='Game Window')
        self.game_widget = GameWidget()
        self.game_accordion.add_widget(self.game_widget)
        self.accordion.add_widget(self.game_accordion)

        self.lobby_accordion = AccordionItem(title='Network')
        self.lobby_widget = NetworkWidget()
        self.lobby_accordion.add_widget(self.lobby_widget)
        self.accordion.add_widget(self.lobby_accordion)

        self.add_widget(self.accordion)
        register(self.focus_game, MatchFocusEvent)
        register(self.show_match_data, MatchEvent)

    def focus_game(self, e):
        self.game_accordion.collapse = False
        self.accordion.select(self.game_accordion)

    def show_match_data(self, me):
        match = me.match
        s = ("%s - %s  %i : %i (%i)"
            % (match.players[WHITE].name, match.players[BLACK].name,
               match.score[WHITE], match.score[BLACK],
               match.length))
        self.game_accordion.title = s

class GameWidget(FloatLayout):
    def __init__(self, **kwargs):
        FloatLayout.__init__(self, **kwargs)

        self.match_widget = MatchWidget(size_hint_y=.9,
            pos_hint={'x': 0, 'y': 0.1})
        button_panel = ButtonPanel(size_hint_y=.1,
            pos_hint={'x': 0, 'y': 0})

        self.add_widget(self.match_widget)
        self.add_widget(button_panel)
        register(self.announce_match_winner, MatchEndEvent)

    def announce_match_winner(self, e):
        points = e.score.values()
        high, low = max(points), min(points)
        verb = "wins" if e.winner.lower() != "you" else "win"
        ok_dialog = OKDialog(text='%s %s %s : %s' % (e.winner, verb, high, low))
        popup = Popup(title='The match has ended',
            content=ok_dialog,
            size_hint=(None, None), size=(400, 400))
        ok_dialog.ok_button.bind(on_press=popup.dismiss)

        popup.open()


class MatchWidget(FloatLayout):
    def __init__(self, **kwargs):
        FloatLayout.__init__(self, **kwargs)

        self.add_widget(Image(source='wood_texture.jpg', pos_hint={'x': 0, 'y': 0},
                              allow_stretch=True, keep_ratio=False))
        self.board = BoardWidget(pos_hint={'x': 0, 'y': 0})
        self.add_widget(self.board)
        self.match = None

        sync_call = GlobalTaskQueue.synced_call
        register(sync_call(self.sync_match), MatchEvent)
        register(sync_call(self.attempt_roll), RollAttemptEvent)
        register(sync_call(self.attempt_commit), CommitAttemptEvent)
        register(sync_call(self.attempt_move), MoveAttemptEvent)
        register(sync_call(self.attempt_double), DoubleAttemptEvent)
        register(sync_call(self.attempt_undo), UndoAttemptEvent)
        register(sync_call(self.attempt_resign), ResignAttemptEvent)

        register(sync_call(self.animate_move), AnimationStartedEvent)
        register(sync_call(self.accept_offer), AcceptEvent)
        register(sync_call(self.announce_game_winner), GameEndEvent)
        register(sync_call(self.suggest_join), JoinChallengeEvent)
        register(sync_call(self.attempt_reject), RejectEvent)
        register(sync_call(self.pause), PauseEvent)

    def sync_match(self, event, on_finish):
        self.match = event.match
        self.board.synchronize(event.match)
        broadcast(MatchFocusEvent())
        on_finish()

    def attempt_move(self, move_attempt_event, on_finish):
        """
        Attempts to execute a move from origin to target.
        If the match allows it, an animation is started independently of the
        event queue. If the move hits a checker, a hit is animated as well.
        """
        origin, target = move_attempt_event.origin, move_attempt_event.target
        if self.match.is_move_possible(origin, target, self.match.color_to_move_next):

            moving_checker, target_spike = self.board.get_animation_data(origin, target)

            if self.match.is_hitting(target):
                hit_checker, target_bar = self.board.get_hit_animation_data(target)
                self.animate_move(moving_checker, target_spike,
                                  lambda: self.animate_move(hit_checker, target_bar, on_finish))
            else:
                self.animate_move(moving_checker, target_spike, on_finish)

            self.match.execute_move(origin, target)
        else:
            Logger.warn("Move from %s to %s not possible" % (origin, target))
            on_finish()

    def attempt_undo(self, undo_att_event, on_finish):
        if not self.match or not self.match.undo_possible(undo_att_event.color):
            Logger.warn("Undo attempt failed - undo not possible")
            on_finish()
            return

        move, hit_color = self.match.undo_move()
        moving_checker, target_spike = self.board.get_animation_data(move.target, move.origin)

        if hit_color:
            hit_checker = self.board.get_bar_checker(hit_color)
            hit_at_spike = self.board._get_spike_by_index(move.target)
            self.animate_move(hit_checker, hit_at_spike,
                              lambda: self.animate_move(moving_checker, target_spike, on_finish))
        else:
            self.animate_move(moving_checker, target_spike, on_finish)

    def attempt_commit(self, commit_attempt_event, on_finish):
        try:
            self.match.commit(commit_attempt_event.color)
        except ValueError, msg:
            Logger.warn(str(msg))
        on_finish()

    def attempt_roll(self, roll_attempt_event, on_finish):
        if self.match:
            self.match.roll(roll_attempt_event.color)
        on_finish()

    def attempt_double(self, double_attempt_event, on_finish):
        if self.match:
            self.match.double(double_attempt_event.color)
        on_finish()

    def attempt_resign(self, resign_attempt_event, on_finish):
        if self.match:
            self.open_resign_dialog(resign_attempt_event.color)
        on_finish()

    def attempt_reject(self, reject_event, on_finish):
        if self.match:
            self.match.reject_open_offer(reject_event.color)
        on_finish()

    def accept_offer(self, accept_event, on_finish):
        if self.match:
            self.match.accept_open_offer(accept_event.color)
        on_finish()

    def pause(self, pe, on_finish):
        Clock.schedule_once(lambda e: on_finish(), pe.ms/1000.0)

    def execute_undo_move(self, undo_move_event, on_finish):
        move = undo_move_event.move
        self.board.get_spikes_for_move_indexes(move.origin,
                                               move.target,
                                               is_undo=True)
        on_finish()

    def announce_game_winner(self, e, on_finish):
        verb = "wins" if e.winner.lower() != "you" else "win"
        point_str = "points" if e.points != 1 else "point"
        ok_dialog = OKDialog(text='The score is now %s : %s' % e.score)
        popup = Popup(title='%s %s %s %s' % (e.winner, verb, e.points, point_str),
                      content=ok_dialog,
                      size_hint=(None, None), size=(400, 400))

        def on_close(evt):
            popup.dismiss()
            on_finish()

        ok_dialog.ok_button.bind(on_press=on_close)

        popup.open()

    def suggest_join(self, event, on_finish):
        dialog = BetweenGamesDialog()
        popup = Popup(title='Continue match?',
            content=dialog,
            size_hint=(None, None), size=(400, 400))

        def on_join(e):
            popup.dismiss()
            broadcast(AcceptJoinEvent())
            on_finish()

        dialog.ok_button.bind(on_press=on_join)

        popup.open()

    def open_resign_dialog(self, resigning_color):
        if self.match.color_to_move_next != resigning_color:
            Logger.info("Not your turn - cannot resign")

        resign_dialog = ResignDialog()
        popup = Popup(title='You resign',
                      content=resign_dialog,
                      size_hint=(None, None),
                      size=(400, 400))

        def on_resign(e):
            choice = resign_dialog.options.choice
            self.match.resignation_points_offered = (resigning_color, choice)
            popup.dismiss()
            broadcast(ResignOfferEvent(resigning_color, choice))

        resign_dialog.ok_button.bind(on_press=on_resign)
        resign_dialog.cancel_button.bind(on_press=popup.dismiss)
        popup.open()

    def animate_move(self, moving_checker, target_spike, on_finish):
        """
        Animate a move of the given checker to the target spike.
        Call the given callback "on_finish" when finished.
        """
        moving_checker.pos_hint = {}

        target_pos = target_spike.get_next_checker_position(moving_checker.model_color)
        size = moving_checker.size

        Logger.warn("Starting animation at %s, queue activity is %s"
                    % (moving_checker.pos, GlobalTaskQueue.running_func))

        new_checker = Checker(moving_checker.model_color,
                              size=size, size_hint=(None, None),
                              pos=moving_checker.pos, pos_hint={})

        if moving_checker.parent:
            moving_checker.parent.remove_widget(moving_checker)

        self.add_widget(new_checker)

        def on_animation_complete(e):
            target_spike.add_checker(moving_checker.model_color)
            self.remove_widget(new_checker)
            on_finish()

        duration = Vector(moving_checker.pos).distance(target_pos)/1000.0
        animation = Animation(pos=target_pos, duration=duration)
        animation.on_complete = on_animation_complete
        animation.start(new_checker)




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
        if cmd:
            Logger.warn("Sending raw command %s" % cmd)
            self.connection.send(cmd)


class BoardApp(App):
    def build(self):
        parent = MainWidget()
        self.bind(on_stop=self.notify_shutdown)
        return parent

    def notify_shutdown(self, e):
        broadcast(GlobalShutdownEvent())

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