import random
from meowbg.core.events import AcceptEvent

from meowbg.core.messaging import broadcast
from meowbg.core.player import AbstractPlayer
from meowbg.gui.guievents import MoveAttemptEvent, CommitAttemptEvent

class Bot(AbstractPlayer):
    def __init__(self, name, color):
        AbstractPlayer.__init__(self, name, color)
        self.match_id = None

    def react(self, match_event):
        match = match_event.match

        if not self.match_id:
            self.match_id = id(match)
        elif self.match_id != id(match):
            # There exists a match other than ours ... get out of here
            self.exit()
            return

        if match.color_to_move_next == self.color:
            print "MY TURN"

            if match.doubling_possible(self.color):
                print "Considering doubling ..."
                if random.random() > 0.01:
                    print "YES, I double"
                    match.double(self.color)
                    return

            match.roll(self.color)

            moves = match.board.find_possible_moves(match.remaining_dice,
                                                   self.color)

            # There may be no possible moves
            if moves:
                mymove = random.choice(moves)
                for m in mymove:
                    broadcast(MoveAttemptEvent(m.origin, m.target))

            broadcast(CommitAttemptEvent(self.color))
        else:
            print "Not my turn!"

    def on_cube(self, cube_event):
        if cube_event.color != self.color:
            broadcast(AcceptEvent(self.color))
