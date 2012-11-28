import logging
from meowbg.core.exceptions import MoveNotPossible
from move import PartialMove
from collections import defaultdict
from operator import lt, gt

BLACK = 1
WHITE = 2
COLOR_NAMES = {WHITE: "White", BLACK: "Black"}
BAR_INDEX = {BLACK: 24, WHITE: -1}
OFF_INDEX = {BLACK: -1, WHITE: 24}
DIRECTION = {BLACK: -1, WHITE: 1}
HOME_INDICES = {WHITE: range(18, 24), BLACK: range(0, 6)}
OUTSIDE_INDICES = {WHITE: range(0, 18), BLACK: range(6, 24)}
OPPONENT = {BLACK: WHITE, WHITE: BLACK}

def index_from_bar(color, distance):
    if color == BLACK:
        return 24 - distance
    else:
        return distance - 1

def home_indices_behind(color, idx):
    cmp_func = gt if color == BLACK else lt
    return [i for i in HOME_INDICES[color] if cmp_func(i, idx)]

logger = logging.getLogger("Board")
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class Board(object):

    # TODO introduce position class and make function accept a single argument
    def __init__(self, on_field=None, on_bar=None, borne_off=None):
        self.init_empty(on_field, on_bar, borne_off)

    def init_empty(self, on_field=None, on_bar=None, borne_off=None):
        self.checkers_on_field = on_field or defaultdict(list)
        self.checkers_on_bar = on_bar or []
        self.borne_off = borne_off or []

        # temporary moves already made but not yet committed
        self.move_stack = []

        # This is recalculated at the beginning of every new move
        self.possible_full_moves_with_initial_dice = []

    def digest_move(self, move):
        """
        Method to be invoked from clients wanting to perform moves.
        May raise exceptions if any legal violations are detected.
        """

        if self.is_legal_partial_move(move):
            self.make_partial_move(move)
        else:
            raise MoveNotPossible("Illegal move: %s" % move)

    def store_initial_possibilities(self, dice, color):
        """
        Calculate the moves that are possible with the given dice and
        color. Empty the move stack first, since this method must be
        invoked only at the beginning of a move.
        """
        self.move_stack = []
        self.possible_full_moves_with_initial_dice = self.find_possible_moves(dice, color)
        logger.warn("Calculated moves for %s with dice %s: %s" % (color, dice, self.possible_full_moves_with_initial_dice))

    def get_remaining_possible_moves(self):
        already_made = [m[0] for m in self.move_stack]
        possible = set([])
        for fm in self.possible_full_moves_with_initial_dice:
            if fm[:len(already_made)] == already_made and len(already_made) != len(fm):
                possible.add(tuple(fm[len(already_made):]))
        return possible

    def is_legal_partial_move(self, partial_move):
        """
        Checks whether a partial move is legal by checking whether
        the current move stack plus the given candidate move yields
        a prefix of a legal full move, i.e. one given in
        self.currently_possible_full_moves.
        """
        candidate_move_stack = [m[0] for m in self.move_stack] + [partial_move]
        for fm in self.possible_full_moves_with_initial_dice:
            if fm[:len(candidate_move_stack)] == candidate_move_stack:
                return True

        logger.error("Move %s would result in move_stack %s, which is not the prefix of any of %s"
                     % (partial_move, candidate_move_stack, self.possible_full_moves_with_initial_dice))
        return False

    def early_commit_possible(self):
        """
        Checks whether the temporary moves stored in the board
        would already be a legal move (even though there may be
        dice remaining ...)
        """

        if not self.possible_full_moves_with_initial_dice:
            # Dancing ... with tears in my eyes
            return True

        moves_from_stack = [m[0] for m in self.move_stack]
        return moves_from_stack in self.possible_full_moves_with_initial_dice

    def _check_possibility(self, move, dice):
        for full_move in self.find_possible_moves(dice, move.color):
            if move in full_move:
                return True
        return False

    def initialize_board(self):
        self.init_empty()
        self.initialize_checkers(BLACK)
        self.initialize_checkers(WHITE)

    def initialize_checkers(self, color):
        idx_1 = 0 if color == WHITE else 23
        self.checkers_on_field[idx_1] = [color] * 2
        idx_2 = 11 if color == WHITE else 12
        self.checkers_on_field[idx_2] = [color] * 5
        idx_3 = 16 if color == WHITE else 7
        self.checkers_on_field[idx_3] = [color] * 3
        idx_4 = 18 if color == WHITE else 5
        self.checkers_on_field[idx_4] = [color] * 5

    def find_possible_moves(self, initial_dice, color):
        """
        Central method to determine the possible 'full' moves for
        a given dice roll. To be consulted for checking moves for
        applicability.
        """

        if len(initial_dice) not in (2, 4):
            raise ValueError("invalid dice %s" % initial_dice)

        moves = []
        if initial_dice[0] != initial_dice[1]:
            # a non-pasch consists of two dice,
            # so consider the swapped dice as well.
            moves.extend(self._find_moves_for_dice(initial_dice, color))
            moves.extend(self._find_moves_for_dice(initial_dice[::-1], color))
        else:
            moves.extend(self._find_moves_for_dice(initial_dice, color))

        if moves:
            moves = self.filter_duplicates(moves)
            moves = self.filter_too_short_moves(moves, color)
            return moves
        else:
            return []

    def _find_moves_for_dice(self, dice, color):
        """
        Method to recursively determine the number of possible
        full moves for the given dice in the given order.
        """

        if not dice:
            return []

        all_moves = []
        sub_moves = self._find_legal_moves_for_die(dice[0], color)
        for sub in sub_moves:
            self.make_partial_move(sub)
            continuations = self._find_moves_for_dice(dice[1:], color)

            if continuations:
                for c in continuations:
                    all_moves.append([sub] + c)
            else:
                all_moves.append([sub])

            self.undo_partial_move()

        return all_moves

    def _find_legal_moves_for_die(self, die, color):
        moves = []
        if color in self.checkers_on_bar:
            mandatory_target_index = index_from_bar(color, die)
            if self.field_accessible_for_color(mandatory_target_index, color):
                moves.append(PartialMove(BAR_INDEX[color], mandatory_target_index))
        else:
            for idx, checkers in self.checkers_on_field.items():
                if color in checkers:
                    target_idx = idx + die if color == WHITE else idx - die
                    if -1 < target_idx < 24:
                        if self.field_accessible_for_color(target_idx, color):
                            moves.append(PartialMove(idx, target_idx))
                    else:
                        # We're checking a move off the board
                        if self.all_checkers_home(color):
                            if target_idx == OFF_INDEX[color]:
                                # non-wasting moves are ok
                                moves.append(PartialMove(idx, target_idx))
                            else:
                                # Look for checkers further behind inside the home than
                                # the currently examined checker. If there is one, then
                                # a wasting move is definitely illegal.
                                move_legal = True
                                for hidx in home_indices_behind(color, idx):
                                    if color in self.checkers_on_field[hidx]:
                                        move_legal = False
                                        break
                                if move_legal:
                                    moves.append(PartialMove(idx, OFF_INDEX[color]))
        return moves


    def field_accessible_for_color(self, idx, color):
        """
        A field at index <idx> is accessible for <color> iff
        there are less than 2 checkers of the opponent's color.
        """
        return self.checkers_on_field[idx].count(OPPONENT[color]) < 2

    def all_checkers_home(self, color):
        """
        Returns True iff no checkers of the given color are
        found outside of this color's home.
        """
        if color in self.checkers_on_bar:
            return False

        for idx in OUTSIDE_INDICES[color]:
            if color in self.checkers_on_field[idx]:
                return False
        return True

    def all_checkers_borne_off(self, color):
        if color in self.checkers_on_bar:
            return False

        for val in self.checkers_on_field.values():
            if color in val:
                return False
        return True

    def make_partial_move(self, move):
        """
        Move a checker from origin to target.
        """
        if move.origin in BAR_INDEX.values():
            color = WHITE if move.target < 6 else BLACK
            self.checkers_on_bar.remove(color)
        else:
            color = self.checkers_on_field[move.origin].pop()

        hit = None
        if move.target == OFF_INDEX[color]:
            self.borne_off.append(color)
        else:
            enemy_count = self.checkers_on_field[move.target].count(OPPONENT[color])
            if enemy_count > 1:
                raise Exception("Move %s is blocked" % move)
            elif enemy_count == 1:
                # pop the hit checker off the target field and append to bar
                hit = self.checkers_on_field[move.target].pop()
                self.checkers_on_bar.append(hit)


            self.checkers_on_field[move.target].append(color)

        self.move_stack.append((move, hit))

    def undo_partial_move(self):
        """
        Undoes a move, reinserting a hit piece if necessary.
        """
        if not self.move_stack:
            raise Exception("No moves to undo")

        last_move, hit_checker = self.move_stack.pop()

        # pop it off the target again ...
        if last_move.target in OFF_INDEX.values():
            color = WHITE if last_move.origin > 17 else BLACK
            self.borne_off.remove(color)
        else:
            color = self.checkers_on_field[last_move.target].pop()

        # ... reinsert at origin
        if last_move.origin == BAR_INDEX[color]:
            self.checkers_on_bar.append(color)
        else:
            self.checkers_on_field[last_move.origin].append(color)

        # ... and reinsert a hit checker, if any
        if hit_checker:
            self.checkers_on_bar.remove(OPPONENT[color])
            self.checkers_on_field[last_move.target].append(OPPONENT[color])

        return last_move, hit_checker

    def get_winner(self):
        for col in (WHITE, BLACK):
            if self.all_checkers_borne_off(col):
                if OPPONENT[col] not in self.borne_off:
                    if OPPONENT[col] in self.checkers_on_bar:
                        return col, 3
                    else:
                        for idx in HOME_INDICES[col]:
                            if OPPONENT[col] in self.checkers_on_field[idx]:
                                return col, 3
                        return col, 2
                else:
                    return col, 1
        return 0, 0


    def check_board_state(self):
        """
        Checks the 'sanity' of a board and raises a ValueError
        if it's invalid (e.g. too few checkers on board etc.)
        """
        all_checkers = []
        for pos, val in self.checkers_on_field.iteritems():
            if val.count(BLACK) and val.count(WHITE):
                raise ValueError("Checkers of both colors at pos %s" % pos)
            all_checkers.extend(val)
        all_checkers.extend(self.checkers_on_bar)
        all_checkers.extend(self.borne_off)

        black = all_checkers.count(BLACK)
        if black != 15:
            raise ValueError("There are %s black checkers on the board" % black)
        white = all_checkers.count(WHITE)
        if white != 15:
            raise ValueError("There are %s white checkers on the board" % white)

    def count_checkers_in_play(self, color):
        """
        Counts checkers of given color still in the game (i.e. on bar or on field)
        """
        on_bar = self.checkers_on_bar.count(color)
        return on_bar + sum([val.count(color) for val in self.checkers_on_field.values()])

    def filter_duplicates(self, moves):
        tuples = [tuple(m) for m in moves]
        return [list(m) for m in set(tuples)]

    def filter_too_short_moves(self, moves, color):
        """
        Usually only the full moves consisting of the maximum number
        of partial moves are actually possible, so we need to sort out
        the bad apples here. A special case are moves winning the game.
        These can occur if the player has one last checker left and
        jumps off the board with a single move instead of two.
        """
        maxlen = max(map(len, moves))
        if self.count_checkers_in_play(color) > 1:
            return [m for m in moves if len(m) == maxlen]
        else:
            return [m for m in moves if len(m) == maxlen
                    or len(m) == 1 and m[0].target == OFF_INDEX[color]]


    def __repr__(self):
        upper_half = []
        for i in range(5):
            line = []
            for j in range(12, 24):
                ch = self.checkers_on_field[j][0] if len(self.checkers_on_field[j]) > i else "_"
                line.append(ch)
            upper_half.append("".join([str(i) for i in line]))

        lower_half = []
        for i in range(4, -1, -1):
            line = []
            for j in range(11, -1, -1):
                ch = self.checkers_on_field[j][0] if len(self.checkers_on_field[j]) > i else "_"
                line.append(ch)
            lower_half.append("".join([str(i) for i in line]))

        return "\n".join(upper_half) + "\n\n" + "\n".join(lower_half)


if __name__ == '__main__':
    b = Board()
    print b