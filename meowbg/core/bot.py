import random
from meowbg.core.events import MatchEvent, CommitAttemptEvent
from meowbg.core.messaging import register, broadcast, unregister
from meowbg.core.player import AbstractPlayer
from meowbg.gui.guievents import MoveAttempt

class Bot(AbstractPlayer):
    def react(self, match_event):
        match = match_event.match
        if match.color_to_move_next == self.color:
            print "MY TURN"

            if match.doubling_possible(self.color):
                print "Considering doubling ..."
                if random.random() > 0.01:
                    print "YES, I double"
                    match.double(self.color)
                    return

            match.roll()

            moves = match.board.find_possible_moves(match.remaining_dice,
                                                   self.color)

            # There may be no possible moves
            if moves:
                mymove = random.choice(moves)
                for m in mymove:
                    broadcast(MoveAttempt(m.origin, m.target))

            broadcast(CommitAttemptEvent())
        else:
            print "Not my turn!"


