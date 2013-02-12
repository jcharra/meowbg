import logging
from meowbg.core.board import Board, WHITE, BLACK, COLOR_NAMES, OPPONENT
from meowbg.core.dice import Dice
from meowbg.core.events import MatchEndEvent, GameEndEvent, RolloutEvent, MatchEvent, SingleMoveEvent, DiceEvent, CommitEvent, RollRequest, CubeEvent, UndoMoveEvent, PendingJoinEvent
from meowbg.core.messaging import broadcast
from meowbg.gui.guievents import HitEvent, UnhitEvent
from move import PartialMove

logger = logging.getLogger("Match")
logger.addHandler(logging.StreamHandler())

class Match(object):

    def __init__(self):
        self.length = 1
        self.finished = False
        self.score = {WHITE: 0, BLACK: 0}
        self.color_to_move_next = None
        self.initial_dice = []
        self.remaining_dice = []
        self.cube = 1
        self.may_double = {WHITE: True, BLACK: True}
        self.players = {WHITE: "", BLACK: ""}
        self.join_pending = {WHITE: False, BLACK: False}

        # This can be either None, BLACK, or WHITE
        self.open_cube_challenge_from_color = None

        # This can either be an empty tuple or a tuple (color, points), e.g. (WHITE, 2)
        self.resignation_points_offered = ()
        self.move_possibilities = []

        self.board = Board()
        # Dice are only for offline games, otherwise
        # they are defined by the server
        self.dice = None

    def roll(self, color):
        if color != self.color_to_move_next:
            logger.warn("It is the turn of color %s, not %s, roll denied" % (self.color_to_move_next, color))
            return

        if self.dice:
            if not self.initial_dice:
                self.initial_dice = self.dice.roll()
                self.remaining_dice = self.initial_dice[:]
                self.board.store_initial_possibilities(self.initial_dice, self.color_to_move_next)
                broadcast(DiceEvent(self.remaining_dice))
            else:
                logger.warn("Cannot roll")
        else:
            broadcast(RollRequest())

    def make_temporary_move(self, origin, target, color):
        if self.color_to_move_next != color:
            logger.warn("Not the turn of " + color)
            return

        hit_event = None
        if OPPONENT[self.color_to_move_next] in self.board.checkers_on_field[target]:
            hit_event = HitEvent(target, self.color_to_move_next)

        move = PartialMove(origin, target)
        self.board.digest_move(move)

        die = self.get_die_for_move(origin, target)
        self.remaining_dice.remove(die)

        broadcast(SingleMoveEvent(move))
        if hit_event:
            broadcast(hit_event)

    def undo(self, color):
        if color != self.color_to_move_next:
            logger.warn("Not your turn, you cannot undo!")
            return

        try:
            move, hit_checker = self.board.undo_partial_move()
        except Exception, msg:
            logger.warn("Undo not possible: %s" % msg)
            return

        die = self.get_die_for_move(move.origin, move.target, undo=True)
        self.remaining_dice.append(die)

        broadcast(UndoMoveEvent(PartialMove(move.target, move.origin)))

        if hit_checker:
            broadcast(UnhitEvent(move.target, hit_checker))

    def get_die_for_move(self, origin, target, undo=False):
        dice = self.remaining_dice if not undo else self.initial_dice
        distance = abs(target - origin)
        for d in range(distance, 7):
            if d in dice:
                return d
        raise ValueError("Cannot find a matching die for %s->%s among %s"
                         % (origin, target, self.remaining_dice))

    def commit(self):
        if self.initial_dice and (not self.remaining_dice or self.board.early_commit_possible()):
            self.initial_dice = self.remaining_dice = []

            pending_moves = [m[0] for m in self.board.flush_move_stack()]
            broadcast(CommitEvent(pending_moves))

            winner, points = self.board.get_winner()
            if winner:
                self.end_game(winner, points)
            else:
                self.switch_turn()
        else:
            raise ValueError("Invalid commit attempted")

    def end_game(self, winner, points):
        points_gained = points * self.cube
        self.score[winner] += points_gained
        winner_name = self.players[winner].name

        if self.score[winner] >= self.length:
            broadcast(MatchEndEvent(winner_name, self.score))
        else:
            self.join_pending = {WHITE: True, BLACK: True}
            broadcast(GameEndEvent(winner_name, points_gained, self.get_score()))
            broadcast(PendingJoinEvent(self))

    def join_next_game(self, color):
        self.join_pending[color] = False
        if True not in self.join_pending.values():
            logger.warn("Game complete")
            self.new_game()
        else:
            logger.warn("Still waiting for %s to accept" % OPPONENT[color])

    def get_score(self):
        return self.score[WHITE], self.score[BLACK]

    def is_crawford(self):
        return self.score[WHITE] != self.score[BLACK] and self.length - 1 in self.score.values()

    def new_game(self):
        logger.warn("New game starting")
        self.cube = 1
        self.dice = Dice()

        self.may_double = {WHITE: not self.is_crawford(), BLACK: not self.is_crawford()}

        d1, d2 = self.dice.rollout()
        self.color_to_move_next = WHITE if d1 > d2 else BLACK

        broadcast(RolloutEvent(d1, d2))

        self.remaining_dice = [d1, d2]
        self.initial_dice = [d1, d2]

        self.board.setup_initial_position()
        self.board.store_initial_possibilities(self.initial_dice, self.color_to_move_next)

        broadcast(MatchEvent(self))

    def double(self, color):
        if self.doubling_possible(color):
            self.open_cube_challenge_from_color = color
            broadcast(CubeEvent(color, self.cube * 2))
        else:
            logger.info("Doubling not allowed")

    def double_accepted(self, by_color):
        self.open_cube_challenge_from_color = None
        self.may_double[by_color] = True
        self.may_double[OPPONENT[by_color]] = False
        self.cube *= 2
        broadcast(MatchEvent(self))

    def accept_open_offer(self, color):
        if color == self.color_to_move_next:
            logger.warn("You cannot accept your own offer")
            return

        if self.open_cube_challenge_from_color:
            self.double_accepted(OPPONENT[self.open_cube_challenge_from_color])
            self.open_cube_challenge_from_color = None
        elif self.resignation_points_offered:
            color, points = self.resignation_points_offered
            self.end_game(color, points)
        else:
            logger.info("No open offers")

    def reject_open_offer(self, color):
        if color == self.color_to_move_next:
            logger.warn("You cannot reject your own offer")
            return
        if self.open_cube_challenge_from_color:
            self.end_game(self.open_cube_challenge_from_color, 1)
            self.open_cube_challenge_from_color = None
        elif self.resignation_points_offered:
            # fire a rejection event here
            self.resignation_points_offered = ()
            broadcast(MatchEvent(self))
        else:
            logger.info("No open offers")

    def doubling_possible(self, color):
        return (self.cube < 64
                and self.remaining_dice == self.initial_dice == []
                and self.may_double[color]
                and self.color_to_move_next == color
                # at least one player's score must still be below the match
                # length if he'd win with the current cube number
                and not all(x + self.cube >= self.length for x in self.score.values()))

    def switch_turn(self):
        if self.color_to_move_next == WHITE:
            self.color_to_move_next = BLACK
        elif self.color_to_move_next == BLACK:
            self.color_to_move_next = WHITE
        else:
            raise ValueError("Noone's turn ... cannot switch")

        broadcast(MatchEvent(self))

    def register_player(self, player, color):
        """
        Register a player to control the pieces
        of the given color
        """
        if self.players[color]:
            self.players[color].exit()

        logger.warn("Registering %s" % player)
        self.players[color] = player

    def __str__(self):
        return ("It is the turn of %s (white: %s, black: %s), dice: %s, board:\n%s"
                % (COLOR_NAMES[self.color_to_move_next],
                   self.players[WHITE],
                   self.players[BLACK],
                   self.remaining_dice,
                   self.board))