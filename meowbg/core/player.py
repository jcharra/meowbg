from meowbg.core.events import MatchEvent, SingleMoveEvent, CommitAttemptEvent, UndoEvent, MoveEvent, ConnectionRequest, CommitEvent, RollRequest
from meowbg.core.messaging import register, unregister, broadcast
from meowbg.network.connectionpool import get_connection

class AbstractPlayer(object):
    def __init__(self, name, color):
        self.name, self.color = name, color
        register(self.react, MatchEvent)

    def exit(self):
        unregister(self.react, MatchEvent)

    def react(self, match_event):
        raise NotImplemented


class HumanPlayer(AbstractPlayer):
    def react(self, match_event):
        """
        Don't to anything automatically, since we expect
        human interaction here.
        """
        pass


class OnlinePlayerProxy(object):
    def __init__(self, name, color, event_translator):
        self.name, self.color = name, color
        self.event_translator = event_translator
        self.connection = None

        register(self.on_commit, CommitEvent)
        register(self.on_roll, RollRequest)

        self.connection = get_connection("Tigergammon")

    def on_commit(self, ce):
        fibs_full_move = self.event_translator.encode(MoveEvent(ce.moves))
        self.connection.send(fibs_full_move)

    def on_roll(self, r):
        cmd = self.event_translator.encode(r)
        self.connection.send(cmd)