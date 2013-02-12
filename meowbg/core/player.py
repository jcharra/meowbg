
from meowbg.core.events import MatchEvent, MoveEvent, CommitEvent, RollRequest, CubeEvent, RejectEvent, AcceptEvent, PendingJoinEvent, JoinChallengeEvent
from meowbg.core.messaging import register, unregister, broadcast
from meowbg.gui.guievents import DoubleAttemptEvent
from meowbg.network.connectionpool import get_connection

class AbstractPlayer(object):
    def __init__(self, name, color):
        self.name, self.color = name, color
        register(self.react, MatchEvent)
        register(self.on_cube, CubeEvent)
        register(self.on_join, PendingJoinEvent)

    def exit(self):
        unregister(self.react, MatchEvent)
        unregister(self.on_cube, MatchEvent)
        unregister(self.on_join, PendingJoinEvent)

    def react(self, match_event):
        raise NotImplemented

    def on_cube(self, cube_event):
        raise NotImplemented

    def on_join(self, join_event):
        raise NotImplemented

class HumanPlayer(AbstractPlayer):
    def react(self, match_event):
        """
        Don't to anything automatically, since we expect
        human interaction here.
        """
        pass

    def on_cube(self, cube_event):
        """
        Same as in react
        """

    def on_join(self, join_event):
        """
        Indicate that a decision in needed here
        """
        broadcast(JoinChallengeEvent(join_event.match, self.color))


class OnlinePlayerProxy(object):
    def __init__(self, name, color, event_translator):
        self.name, self.color = name, color
        self.event_translator = event_translator
        self.connection = None

        register(self.on_commit, CommitEvent)
        register(self.on_default, RollRequest)
        register(self.on_default, DoubleAttemptEvent)
        register(self.on_default, AcceptEvent)
        register(self.on_default, RejectEvent)

        self.connection = get_connection("Tigergammon")

    def on_commit(self, ce):
        fibs_full_move = self.event_translator.encode(MoveEvent(ce.moves))
        self.connection.send(fibs_full_move)

    def on_default(self, r):
        cmd = self.event_translator.encode(r)
        self.connection.send(cmd)

    def exit(self):
        unregister(self.on_commit, CommitEvent)
        unregister(self.on_default, RollRequest)
        unregister(self.on_default, DoubleAttemptEvent)
        unregister(self.on_default, AcceptEvent)
        unregister(self.on_default, RejectEvent)
        self.connection = None