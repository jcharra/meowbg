import random
from meowbg.core.events import MatchEvent, MoveEvent, CommitEvent
from meowbg.core.messaging import register, broadcast
from meowbg.gui.guievents import MoveAttempt

class Bot(object):
    def __init__(self, color):
        self.color = color
        self.callback = None
        register(self.react, MatchEvent)

    def react(self, match_event):
        match = match_event.match
        if match.color_to_move_next == self.color:
            print "MY TURN"
            moves = match.board.find_possible_moves(match.remaining_dice,
                                                   self.color)

            # There may be no possible moves
            if moves:
                mymove = random.choice(moves)
                for m in mymove:
                    broadcast(MoveAttempt(m.origin, m.target))

            broadcast(CommitEvent(self.color))
        else:
            print "Not my turn!"


