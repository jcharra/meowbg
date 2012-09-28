import logging
from meowbg.core.board import Board, WHITE, BLACK, COLOR_NAMES, OPPONENT
from meowbg.core.dice import Dice
from meowbg.core.events import MatchEndEvent, GameEndEvent, RolloutEvent, MatchEvent, SingleMoveEvent, DiceEvent
from meowbg.core.messaging import broadcast
from meowbg.gui.guievents import HitEvent
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
        self.color_to_move_next = None
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
        if self.color_to_move_next != color:
            logger.warn("Not the turn of " + color)
            return

        hit_event = None
        if OPPONENT[self.color_to_move_next] in self.board.checkers_on_field[target]:
            hit_event = HitEvent(target, self.color_to_move_next)

        move = PartialMove(origin, target)
        self.board.digest_move(move)

        # Move was legal, so broadcast hit event now
        if hit_event:
            broadcast(hit_event)

        die = self.get_die_for_move(origin, target)
        self.remaining_dice.remove(die)

        broadcast(SingleMoveEvent(move))

    def get_die_for_move(self, origin, target):
        die = abs(target - origin)
        for d in range(die, 7):
            if d in self.remaining_dice:
                return d
        raise ValueError("Cannot find a matching die for %s->%s among %s"
                         % (origin, target, self.remaining_dice))

    def _commit_possible(self, color):
        if self.color_to_move_next != color:
            logger.warn("Cannot commit for %s when it's %s's turn" %
                        (COLOR_NAMES[color], COLOR_NAMES[self.color_to_move_next]))
            return False
        elif not self.remaining_dice:
            return True
        else:
            logger.warn("Dice remaining: %s ... ask board if it's ok" % self.remaining_dice)
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
            self.color_to_move_next = WHITE
        else:
            self.color_to_move_next = BLACK

        broadcast(RolloutEvent(d1, d2))

        self.remaining_dice = [d1, d2]
        self.initial_dice = [d1, d2]

        broadcast(DiceEvent(self.remaining_dice, self.color_to_move_next))

        self.board.initialize_board()
        self.board.store_initial_possibilities(self.initial_dice, self.color_to_move_next)

        broadcast(MatchEvent(self))

    def doubling_possible(self, color):
        return (self.remaining_dice == self.initial_dice
                and self.may_double[color]
                and self.color_to_move_next == color)

    def switch_turn(self):
        self.initial_dice = self.dice.roll()
        self.remaining_dice = self.initial_dice[:]

        if self.color_to_move_next == WHITE:
            self.color_to_move_next = BLACK
        elif self.color_to_move_next == BLACK:
            self.color_to_move_next = WHITE
        else:
            raise ValueError("Noone's turn ... cannot switch")

        self.board.store_initial_possibilities(self.initial_dice, self.color_to_move_next)

        broadcast(DiceEvent(self.remaining_dice, self.color_to_move_next))
        broadcast(MatchEvent(self))

    def __str__(self):
        return ("It is the turn of %s (white: %s, black: %s), dice: %s, board:\n%s"
                % (COLOR_NAMES[self.color_to_move_next],
                   self.player_names[WHITE],
                   self.player_names[BLACK],
                   self.remaining_dice,
                   self.board))