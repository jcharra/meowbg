import logging
from meowbg.core.board import Board
from move import PartialMove
from board import BLACK, WHITE

class Match(object):
    logger = logging.getLogger("Match")

    def __init__(self):
        """
        As lean as possible ... if later we "feed" the instance with an actual
        match standing, everything done here would be rendered useless anyway.
        """
        self.player_names = []
        self.length = 1
        self.score = [0, 0]
        self.turn = None
        self.players_dice = []
        self.players_remaining_dice = []
        self.opponents_dice = []
        self.cube = 1
        self.player_may_double = 0
        self.opponent_may_double = 0
        self.was_doubled = 0
        self.players_color = WHITE
        self.opponents_color = BLACK
        self.players_direction = -1
        self.move_possibilities = []

        self.initially_possible_moves = []
        self.board = Board()
        self.observers = []
        self.event_listener = None

    def make_temporary_move(self, origin, die):
        if self.turn != self.players_color:
            self.logger.warn("Not your turn")
            return

        target = origin + self.players_direction * die
        move = PartialMove(self.players_color, origin, target)

        self.board.digest_move(move, die)
        self.players_remaining_dice.remove(die)

    def commit_possible(self):
        if self.turn != self.players_color:
            return False
        elif not self.players_remaining_dice:
            return True
        else:
            return self.board.commit_possible(self.initially_possible_moves)

    def doubling_possible(self):
        return (self.players_remaining_dice == self.players_dice
                and self.player_may_double
                and self.turn == self.players_color)

    def switch_turn(self):
        if self.turn == self.players_color:
            self.turn = self.opponents_color
        elif self.turn == self.opponents_color:
            self.turn = self.players_color
        else:
            raise ValueError("Noone's turn ... cannot switch")

    def __str__(self):
        return ("Dice player (%s): %s, dice opponent (%s): %s, turn: %s"
                % (self.players_color, self.players_remaining_dice,
                   self.opponents_color, self.opponents_dice, self.turn))