import random
from meowbg.core.events import AcceptEvent, ResignOfferEvent, MatchEvent, CubeEvent

from meowbg.core.messaging import broadcast, register, unregister
from meowbg.core.player import Player
from meowbg.gui.guievents import MoveAttemptEvent, CommitAttemptEvent, DoubleAttemptEvent


class Bot(Player):
    def __init__(self, name, color):
        Player.__init__(self, name, color)
        self.match_id = None
        register(self.on_resign, ResignOfferEvent)
        register(self.react, MatchEvent)
        register(self.on_cube, CubeEvent)

    def react(self, match_event):
        match = match_event.match

        if not self.match_id:
            self.match_id = id(match)
        elif self.match_id != id(match):
            # There exists a match other than ours ... get out of here
            self.exit()
            return

        if match.color_to_move_next == self.color:
            if match.doubling_possible(self.color):
                if random.random() > 1.01:
                    broadcast(DoubleAttemptEvent(self.color))
                    return

            match.roll(self.color)

            moves = match.board.find_possible_moves(match.remaining_dice,
                                                    self.color)

            # There may be no possible moves
            if moves:
                mymove = random.choice(moves)
                for m in mymove:
                    #match.execute_move(m.origin, m.target, self.color)
                    broadcast(MoveAttemptEvent(m.origin, m.target))

            broadcast(CommitAttemptEvent(self.color))
        else:
            print "Not my turn!"

    def on_cube(self, cube_event):
        if cube_event.color != self.color:
            broadcast(AcceptEvent(self.color))

    def on_resign(self, event):
        if event.color != self.color:
            broadcast(AcceptEvent(self.color))

    def exit(self):
        unregister(self.on_resign, ResignOfferEvent)
        unregister(self.react, MatchEvent)
        unregister(self.on_cube, CubeEvent)

    def __repr__(self):
        return "Bot '%s'" % self.name
