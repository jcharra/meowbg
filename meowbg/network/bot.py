import random
from kivy.logger import Logger
from meowbg.core.dice import Dice
from meowbg.core.match import Match
from meowbg.network.events import MatchEvent, MoveEvent, RolloutEvent, DiceEvent, SingleMoveEvent

class Bot(object):
    def __init__(self):
        self.dice = Dice()
        self.callback = None

    def handle(self, event):
        if isinstance(event, MatchEvent):
            self.match = event.match
        elif isinstance(event, MoveEvent):
            for m in event.moves:
                self.match.board.make_partial_move(m)
        else:
            Logger.info("Cryptic event: %s" % event)

        Logger.info("Match is %s" % self.match)
        self.react()

    def notify(self, event):
        if self.callback:
            self.callback(event)
        else:
            print "Event %s went unnoticed ..." % event

    def pick_move(self):
        moves = self.match.board.get_possible_moves(self.match.opponents_dice,
                                                    self.match.opponents_color)
        mymove = random.choice(moves)
        self.notify(MoveEvent(mymove))
        self.match.opponents_dice = []

    def react(self):
        if self.match.turn == self.match.opponents_color:

            self.match.opponents_dice = self.dice.roll()
            self.notify(DiceEvent(self.match.opponents_dice, self.match.opponents_color))
            self.pick_move()
            self.match.switch_turn()
            self.react()

        elif self.match.turn == self.match.players_color:

            self.match.players_remaining_dice = self.dice.roll()
            self.notify(DiceEvent(self.match.players_remaining_dice, self.match.players_color))

        else:
            # initially we need to "echo" the match back
            self.notify(MatchEvent(self.match))
            d1, d2 = self.dice.rollout()
            self.notify(RolloutEvent(d1, d2))

            if d1 > d2:
                self.match.turn = self.match.players_color
                self.match.players_remaining_dice = [d1, d2]
                self.notify(DiceEvent([d1, d2], self.match.players_color))
            else:
                self.match.turn = self.match.opponents_color
                self.react()