from meowbg.core.events import MatchEvent, SingleMoveEvent, CommitEvent
from meowbg.core.messaging import register, unregister

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
    def __init__(self, name, color, event_translator, connection=None):
        self.name, self.color = name, color
        self.event_translator = event_translator
        self.connection = connection
        self.pending_moves = []

        # listen to all kinds of events
        register(self.on_move, SingleMoveEvent)
        register(self.on_commit, CommitEvent)

    def on_move(self, me):
        self.pending_moves.append(me.move)

    def on_commit(self, ce):
        pass

    def listen_to_connection(self, conn):
        self.connection = conn
