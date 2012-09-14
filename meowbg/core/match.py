import logging
from meowbg.core.board import Board, WHITE, BLACK, COLOR_NAMES
from meowbg.core.dice import Dice
from meowbg.core.events import MatchEndEvent, GameEndEvent, RolloutEvent, MatchEvent, SingleMoveEvent, DiceEvent
from meowbg.core.messaging import broadcast
from move import PartialMove
from board import DIRECTION

logger = logging.getLogger("Match")
logger.addHandler(logging.StreamHandler())

class Match(object):

    def __init__(self):
        """
        As lean as possible ... if later we "feed" the instance with an actual
        match standing, everything done here would be rendered useless anyway.
        """
        self.length = 1
        self.score = {WHITE: 0, BLACK: 0}
        self.turn = None
        self.initial_dice = []
        self.remaining_dice = []
        self.cube = 1
        self.may_double = {WHITE: True, BLACK: True}
        self.player_names = {WHITE: "", BLACK: ""}
        self.was_doubled = 0
        self.move_possibilities = []
        self.initially_possible_moves = []

        self.dice = Dice()
        self.board = Board()

    def make_temporary_move(self, origin, target, color):
        if self.turn != color:
            logger.warn("Not the turn of " + color)
            return

        move = PartialMove(origin, target)

        self.board.digest_move(move)
        self.remaining_dice.remove(self.get_die_for_move(origin, target))

        broadcast(SingleMoveEvent(move))

    def get_die_for_move(self, origin, target):
        die = abs(target - origin)
        for d in range(die, 7):
            if d in self.remaining_dice:
                return d
        raise ValueError("Cannot find a matching die for %s->%s among %s"
                         % (origin, target, self.remaining_dice))

    def _commit_possible(self, color):
        if self.turn != color:
            return False
        elif not self.remaining_dice:
            return True
        else:
            return self.board.commit_possible()

    def commit(self, color):
        if self._commit_possible(color):
            winner, points = self.board.get_winner()
            if winner:
                broadcast(GameEndEvent(winner, points))
                self.score[winner] += points * self.cube
                if self.score[winner] >= self.length:
                    broadcast(MatchEndEvent(winner, self.score))
                else:
                    self.new_game()
            else:
                self.switch_turn()
        else:
            logger.warn("Invalid commit attempted")


    def is_crawford(self):
        return (self.score[WHITE] == self.length - 1 and self.score[BLACK] != self.length - 1
             or self.score[BLACK] == self.length - 1 and self.score[WHITE] != self.length - 1)

    def new_game(self):
        logger.warn("New game starting")
        self.cube = 1
        self.may_double = {WHITE: not self.is_crawford(), BLACK: not self.is_crawford()}

        d1, d2 = self.dice.rollout()
        if d1 > d2:
            self.turn = WHITE
        else:
            self.turn = BLACK

        broadcast(RolloutEvent(d1, d2))

        self.remaining_dice = [d1, d2]
        self.initial_dice = [d1, d2]

        broadcast(DiceEvent(self.remaining_dice, self.turn))

        self.board.initialize_board()
        self.board.store_initial_possibilities(self.initial_dice, self.turn)

        broadcast(MatchEvent(self))

    def doubling_possible(self, color):
        return (self.remaining_dice == self.initial_dice
                and self.may_double[color]
                and self.turn == color)

    def switch_turn(self):
        self.initial_dice = self.dice.roll()
        self.remaining_dice = self.initial_dice[:]

        if self.turn == WHITE:
            self.turn = BLACK
        elif self.turn == BLACK:
            self.turn = WHITE
        else:
            raise ValueError("Noone's turn ... cannot switch")

        self.board.store_initial_possibilities(self.initial_dice, self.turn)

        broadcast(DiceEvent(self.remaining_dice, self.turn))
        broadcast(MatchEvent(self))

    def __str__(self):
        return ("It is the turn of %s (white: %s, black: %s), dice: %s, board:\n%s"
                % (COLOR_NAMES[self.turn],
                   self.player_names[WHITE],
                   self.player_names[BLACK],
                   self.remaining_dice,
                   self.board))