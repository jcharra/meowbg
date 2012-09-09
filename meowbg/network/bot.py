import random
from meowbg.core.events import MatchEvent, MoveEvent, CommitEvent
from meowbg.core.messaging import register, broadcast

class Bot(object):
    def __init__(self, color):
        self.color = color
        self.callback = None
        register(self.react, MatchEvent)

    def react(self, match_event):
        match = match_event.match
        if match.turn == self.color:
            moves = match.board.get_possible_moves(match.remaining_dice,
                                                   self.color)
            mymove = random.choice(moves)
            broadcast(MoveEvent(mymove))
            broadcast(CommitEvent())
        else:
            print "Not my turn!"

