import random
from kivy.logger import Logger
from meowbg.core.dice import Dice
from meowbg.core.match import Match
from meowbg.network.events import MatchEvent, MoveEvent, RolloutEvent, DiceEvent

class Bot(object):
    def __init__(self):
        self.dice = Dice()
        self.match = Match()
        self.callback = None
        self.name = random.choice(["Albert", "Klaus", "Antje"])

        self.match.player_names.append(self.name)

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

    def react(self):
        if self.match.turn is None:
            d1, d2 = self.dice.rollout()

            self.notify(RolloutEvent(d1, d2))

            if d2 > d1:
                self.match.turn = self.match.players_color
                self.match.players_dice = [d1, d2]
                self.match.players_remaining_dice = [d1, d2]
                Logger.info("You win the rollout, match is %s" % self.match)
            else:
                self.match.turn = self.match.opponents_color
                self.match.opponents_dice = [d1, d2]
                Logger.info("I win the rollout, match is %s" % self.match)

            self.notify(MatchEvent(self.match))
            self.react()
        elif self.match.turn == self.match.opponents_color:
            Logger.info("My turn, let's see ... match is %s" % self.match)
            moves = self.match.board.get_possible_moves(self.match.opponents_dice,
                                                        self.match.opponents_color)
            mymove = random.choice(moves)
            self.notify(MoveEvent(mymove))

            self.match.opponents_dice = []
            self.match.players_remaining_dice = self.dice.roll()
            self.notify(DiceEvent(self.match.players_remaining_dice))

            self.match.turn = self.match.players_color

            self.notify(MatchEvent(self.match))
        else:
            print "It's not my turn"

