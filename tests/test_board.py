
import unittest
from itertools import product
from meowbg.core.board import Board, BLACK, WHITE
from meowbg.core.exceptions import MoveNotPossible
from meowbg.core.move import PartialMove
from collections import defaultdict


class BoardTestCase(unittest.TestCase):
    def setUp(self):
        self.board = Board()

    def test_initial_board(self):
        self.board.setup_initial_position()

        try:
            self.board.check_board_state()
        except ValueError, msg:
            assert False, "Board should be ok initially, got: %s" % msg

        # Take away a checker from the white ones
        self.board.checkers_on_field[0].pop()
        try:
            self.board.check_board_state()
            assert False, "Board recognized as valid, though invalid"
        except ValueError:
            # exception ok here
            pass

        # Add back two more
        self.board.checkers_on_field[0].extend([WHITE] * 2)
        try:
            self.board.check_board_state()
            assert False, "Board recognized as valid, though invalid"
        except ValueError:
            # exception ok here
            pass

        # Take one away again => valid board again
        self.board.checkers_on_field[0].pop()
        try:
            self.board.check_board_state()
        except ValueError, msg:
            assert False, "Board should be ok again, got: %s" % msg

        # Mix stones
        stone = self.board.checkers_on_field[0].pop()
        self.board.checkers_on_field[5].append(stone)
        try:
            self.board.check_board_state()
            assert False, "Board recognized as valid, though invalid"
        except ValueError:
            # exception ok here
            pass

    def test_find_legal_moves_for_die_basic(self):
        self.board.setup_initial_position()

        legal_moves = self.board._find_legal_moves_for_die(1, BLACK)
        self.assertEquals(len(legal_moves), 3)
        legal_moves = self.board._find_legal_moves_for_die(2, BLACK)
        self.assertEquals(len(legal_moves), 4)
        legal_moves = self.board._find_legal_moves_for_die(3, BLACK)
        self.assertEquals(len(legal_moves), 4)
        legal_moves = self.board._find_legal_moves_for_die(4, BLACK)
        self.assertEquals(len(legal_moves), 4)
        legal_moves = self.board._find_legal_moves_for_die(5, BLACK)
        self.assertEquals(len(legal_moves), 2)
        legal_moves = self.board._find_legal_moves_for_die(6, BLACK)
        self.assertEquals(len(legal_moves), 3)

        legal_moves = self.board._find_legal_moves_for_die(1, WHITE)
        self.assertEquals(len(legal_moves), 3)
        legal_moves = self.board._find_legal_moves_for_die(2, WHITE)
        self.assertEquals(len(legal_moves), 4)
        legal_moves = self.board._find_legal_moves_for_die(3, WHITE)
        self.assertEquals(len(legal_moves), 4)
        legal_moves = self.board._find_legal_moves_for_die(4, WHITE)
        self.assertEquals(len(legal_moves), 4)
        legal_moves = self.board._find_legal_moves_for_die(5, WHITE)
        self.assertEquals(len(legal_moves), 2)
        legal_moves = self.board._find_legal_moves_for_die(6, WHITE)
        self.assertEquals(len(legal_moves), 3)

    def test_find_legal_moves_for_die_advanced(self):
        self.board.checkers_on_field.update({4: [BLACK], 3: [BLACK]})
        legal_moves = self.board._find_legal_moves_for_die(3, BLACK)
        self.assertEquals(len(legal_moves), 2)
        legal_moves = self.board._find_legal_moves_for_die(5, BLACK)
        self.assertEquals(len(legal_moves), 1)
        legal_moves = self.board._find_legal_moves_for_die(6, BLACK)
        self.assertEquals(len(legal_moves), 1)

        self.board.checkers_on_field.update({20: [WHITE], 21: [WHITE]})
        legal_moves = self.board._find_legal_moves_for_die(3, WHITE)
        self.assertEquals(len(legal_moves), 2)
        legal_moves = self.board._find_legal_moves_for_die(5, WHITE)
        self.assertEquals(len(legal_moves), 1)
        legal_moves = self.board._find_legal_moves_for_die(6, WHITE)
        self.assertEquals(len(legal_moves), 1)


    def test_all_checkers_home(self):
        # positive case 1
        self.board.checkers_on_field.update({4: [BLACK], 3: [BLACK]})
        self.assertTrue(self.board.all_checkers_home(BLACK))
        # bar must not contain black checkers
        self.board.checkers_on_bar.append(BLACK)
        self.assertFalse(self.board.all_checkers_home(BLACK))
        self.board.checkers_on_bar = []
        # and no checker outside the home
        self.board.checkers_on_field.update({6: [BLACK]})
        self.assertFalse(self.board.all_checkers_home(BLACK))

        # Same for white

        # positive case 1
        self.board.checkers_on_field.update({20: [WHITE], 21: [WHITE]})
        self.assertTrue(self.board.all_checkers_home(WHITE))
        # no white checkers on bar
        self.board.checkers_on_bar.append(WHITE)
        self.assertFalse(self.board.all_checkers_home(WHITE))
        self.board.checkers_on_bar = []
        # and no checker outside the home
        self.board.checkers_on_field.update({6: [WHITE]})
        self.assertFalse(self.board.all_checkers_home(WHITE))

    def test_find_moves_for_dice(self):
        self.board.checkers_on_field.update({20: [WHITE], 21: [WHITE]})
        dice = [4, 3]
        full_moves = self.board._find_moves_for_dice(dice, WHITE)
        self.assertEquals(len(full_moves), 1)
        self.assertTrue(all([m.target == 24 for m in full_moves[0]]))

    def test_find_legal_short_move(self):
        # If a move finished the game, it may consist of a lower
        # number of partial moves than the longest possible move.
        self.board.checkers_on_field.update({18: [WHITE]})
        dice = [6, 1]
        full_moves = self.board.find_possible_moves(dice, WHITE)
        self.assertEqual(len(full_moves), 2)
        self.assertEqual(min(map(len, full_moves)), 1)

    def test_find_moves_for_dice_symmetry(self):
        self.board.setup_initial_position()

        for dice in product(range(1, 7), repeat=2):
            moves_white = self.board._find_moves_for_dice(dice, WHITE)
            moves_black = self.board._find_moves_for_dice(dice, BLACK)
            self.assertEquals(len(moves_white), len(moves_black),
                              "Failure for %s: %s asymmetric to %s" % (dice, moves_white, moves_black))

    def test_initial_moves_for_dice(self):
        self.board.setup_initial_position()

        dice = [5, 6]
        full_moves = self.board._find_moves_for_dice(dice, WHITE)

    def test_make_and_undo_partial_move(self):
        self.board.setup_initial_position()
        self.board.checkers_on_field.update({4: [WHITE]})
        move = PartialMove(5, 4)
        self.board.make_partial_move(move)

        # hit checker should be on bar and no longer on board
        self.assertEqual(self.board.checkers_on_field[4], [BLACK])
        self.assertEqual(self.board.checkers_on_bar, [WHITE])

        self.board.undo_partial_move()

        # hit checker should be off the bar and back on board
        self.assertEqual(self.board.checkers_on_field[5], [BLACK, BLACK, BLACK, BLACK, BLACK])
        self.assertEqual(self.board.checkers_on_field[4], [WHITE])
        self.assertEqual(self.board.checkers_on_bar, [])

    def test_make_and_undo_move_off_board(self):
        onfield = defaultdict(list)
        onfield[4] = [BLACK]
        self.board.set_board(onfield)

        borne_off_before = len(self.board.borne_off)

        move = PartialMove(4, -1)
        self.board.make_partial_move(move)

        self.assertEqual(self.board.checkers_on_field[4], [])
        self.assertEqual(len(self.board.borne_off), borne_off_before + 1)

        self.board.undo_partial_move()

        self.assertEqual(self.board.checkers_on_field[4], [BLACK])
        self.assertEqual(len(self.board.borne_off), borne_off_before)

    def test_make_and_undo_move_off_bar(self):
        self.board.checkers_on_bar = [BLACK]
        self.board.checkers_on_field.update({20: [WHITE]})
        move = PartialMove(24, 20)
        self.board.make_partial_move(move)

        self.assertEqual(self.board.checkers_on_field[20], [BLACK])
        self.assertEqual(self.board.checkers_on_bar, [WHITE])

        self.board.undo_partial_move()

        self.assertEqual(self.board.checkers_on_field[20], [WHITE])
        self.assertEqual(self.board.checkers_on_bar, [BLACK])

    def test_get_winner(self):
        # Backgammon
        onfield = defaultdict(list)
        onfield[1] = [WHITE] * 14
        self.board.set_board(onfield, on_bar=[WHITE])
        self.assertEqual(self.board.get_winner(), (BLACK, 3))

        # Gammon
        onfield = defaultdict(list)
        onfield[23] = [WHITE] * 15
        self.board.set_board(onfield, on_bar=[])
        self.assertEqual(self.board.get_winner(), (BLACK, 2))

        # Normal victory (one already borne off)
        onfield = defaultdict(list)
        onfield[23] = [WHITE] * 13
        self.board.set_board(onfield, on_bar=[WHITE])
        self.assertEqual(self.board.get_winner(), (BLACK, 1))

        # No winner yet
        self.board.checkers_on_field.update({1: [BLACK], 23: [WHITE]})
        self.assertEqual(self.board.get_winner(), (0, 0))

    def test_try_illegal_moves(self):
        self.board.checkers_on_field.update({6: [BLACK], 4: [BLACK],
                                        3: [WHITE, WHITE], 0: [WHITE, WHITE]})
        illegal_move = PartialMove(6, 3)
        try:
            self.board.digest_move(illegal_move)
            assert False, "Move %s should be impossible" % illegal_move
        except MoveNotPossible:
            # An exception is the desired result here
            pass

    def test_fill_initial_possibilities(self):
        self.board.checkers_on_field.update({10: [BLACK, BLACK], 20: [WHITE]})
        self.board.store_initial_possibilities([5, 6], BLACK)
        expected = [PartialMove(10, 5), PartialMove(10, 4)]
        self.assertEqual([expected, expected[::-1]], self.board.possible_full_moves_with_initial_dice)

        self.board.store_initial_possibilities([5, 6], WHITE)
        self.assertEqual([[PartialMove(20, 24)]], self.board.possible_full_moves_with_initial_dice)

    def test_digest_move(self):
        self.board.checkers_on_field.update({10: [BLACK, BLACK]})
        m = PartialMove(10, 4)

if __name__ == '__main__':
    unittest.main()
