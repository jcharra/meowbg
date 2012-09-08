import random
from kivy.logger import Logger
from meowbg.core.events import MatchEvent, MoveEvent, DiceEvent

class Bot(object):
    def __init__(self, color):
        self.color = color
        self.callback = None

    def handle(self, event):
        if isinstance(event, MatchEvent):
            self.react(event.match)
        else:
            Logger.info("Cryptic event: %s" % event)

    def notify(self, event):
        if self.callback:
            self.callback(event)
        else:
            print "Event %s went unnoticed ..." % event

    def react(self, match):
        if match.turn == self.color:
            moves = match.board.get_possible_moves(match.opponents_dice,
                                                   match.opponents_color)
            mymove = random.choice(moves)
            self.notify(MoveEvent(mymove))
        else:
            print "Not my turn!"

