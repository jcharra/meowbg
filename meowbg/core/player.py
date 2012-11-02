from meowbg.core.events import MatchEvent, SingleMoveEvent, CommitEvent, UndoEvent, MoveEvent, ConnectionRequest
from meowbg.core.messaging import register, unregister, broadcast

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

        # These are the moves of the opponent, NOT the
        # player's that this proxy represents.
        self.recorded_moves = []
        # Consequently, we need to know whether moves that
        # occur are our own or the opponent's, to know
        # whether we ought to be recording those or not.
        self.recording = False

        register(self.on_match, MatchEvent)
        register(self.on_commit, CommitEvent)
        register(self.on_move, SingleMoveEvent)
        register(self.on_undo, UndoEvent)

        broadcast(ConnectionRequest("Tigergammon", self.set_connection))

    def set_connection(self, conn):
        print "Connection set to %s" % conn
        self.connection = conn

    def on_match(self, me):
        self.recording = (me.match.color_to_move_next != self.color)

    def on_move(self, me):
        self.recorded_moves.append(me.move)

    def on_undo(self, ue):
        self.recorded_moves.pop()

    def on_commit(self, ce):
        fibs_full_move = self.event_translator.encode(MoveEvent(self.recorded_moves))
        print "Committing move %s" % fibs_full_move
        self.connection.send(fibs_full_move)
        self.recorded_moves = []

    def listen_to_connection(self, conn):
        self.connection = conn
