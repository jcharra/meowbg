
import logging
from meowbg.core.events import (MoveEvent, CommitEvent, RollRequest,
                                RejectEvent, AcceptEvent, ResignOfferEvent,
                                OpponentJoinedEvent)
from meowbg.core.messaging import register, unregister
from meowbg.gui.guievents import DoubleAttemptEvent
from meowbg.network.connectionpool import get_connection

logger = logging.getLogger("Player")
logger.addHandler(logging.StreamHandler())


class Player(object):
    def __init__(self, name, color):
        self.name, self.color = name, color

    def exit(self):
        pass

    def __repr__(self):
        return "%s '%s'" % (self.__class__, self.name)


class HumanPlayer(Player):
    """
    Pretty much just a "marker class" yet :)
    """


class OnlinePlayerProxy(object):
    def __init__(self, name, color, event_translator):
        self.name, self.color = name, color
        self.event_translator = event_translator

        register(self.on_commit, CommitEvent)
        register(self.on_default, RollRequest)
        register(self.on_default, AcceptEvent)
        register(self.on_default, RejectEvent)
        register(self.on_default, ResignOfferEvent)
        register(self.on_default, DoubleAttemptEvent)

        self.connection = get_connection()

    def on_commit(self, ce):
        fibs_full_move = self.event_translator.encode(MoveEvent(ce.moves))
        self.connection.send(fibs_full_move)

    def on_default(self, r):
        if hasattr(r, 'color') and r.color == self.color:
            logger.error("This was triggered by me ... ignoring")
            return

        cmd = self.event_translator.encode(r)
        self.connection.send(cmd)

    def exit(self):
        unregister(self.on_commit, CommitEvent)
        unregister(self.on_default, RollRequest)
        unregister(self.on_default, AcceptEvent)
        unregister(self.on_default, RejectEvent)
        unregister(self.on_default, ResignOfferEvent)
        unregister(self.on_default, DoubleAttemptEvent)
        self.connection = None

    def __repr__(self):
        return "Proxy for '%s'" % self.name