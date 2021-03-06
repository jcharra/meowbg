
import unittest
from meowbg.network.translation import FIBSTranslator, translate_move_to_indexes, translate_indexes_to_move
from meowbg.core.match import Match
from meowbg.core.board import BLACK, WHITE
from meowbg.core.player import HumanPlayer

TESTLINE_STATUS_1 = ("5 someplayer evil_guy - 0 0 1418.61 23 1914 1041272421 192.168.40.3 "
                     "meowBG someplayer@somewhere.com")
TESTLINE_STATUS_2 = ("5 peter paul - 0 0 1918.61 23 1914 1041272421 192.168.40.3 "
                     "meowBG someplayer@somewhere.com")
TESTLINE_STATUS_3 = ("5 michael_romeo russell_allen - 0 0 1418.61 23 1914 1041272421 192.168.40.3 "
                     "meowBG someplayer@somewhere.com")

TESTLINE_MOVE_1 = "opponent moves 12-3 4-off 3-off"
TESTLINE_MOVE_2 = "opponent moves bar-23"

class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = FIBSTranslator()
        m = Match()
        m.players[WHITE] = HumanPlayer("P1", WHITE)
        m.players[BLACK] = HumanPlayer("opponent", BLACK)
        m.color_to_move_next = BLACK
        self.parser.current_match = m

    def test_parse_line_to_args_player_status(self):
        args = self.parser.parse_line_to_args(TESTLINE_STATUS_1, line_type=self.parser.PLAYER_STATUS_EVENT)
        self.assertEquals(args["name"], "someplayer")
        self.assertEquals(args["opponent"], "evil_guy")
        self.assertEquals(args["watching"], "-")
        self.assertEquals(args["ready"], "0")
        self.assertEquals(args["away"], "0")
        self.assertEquals(args["rating"], "1418.61")
        self.assertEquals(args["experience"], "23")
        self.assertEquals(args["idle"], "1914")
        self.assertEquals(args["login"], "1041272421")
        self.assertEquals(args["hostname"], "192.168.40.3")
        self.assertEquals(args["client"], "meowBG")
        self.assertEquals(args["email"], "someplayer@somewhere.com")

    def test_parse_events_multiline_status(self):
        test_input = "\r\n".join((TESTLINE_STATUS_1, TESTLINE_STATUS_2, TESTLINE_STATUS_3, "6"))
        status_events = self.parser.parse_events(test_input)
        self.assertEqual(1, len(status_events))
        dicts = status_events[0].status_dicts
        first = dicts[0]
        self.assertEqual(first["name"], "someplayer")
        self.assertEqual(first["opponent"], "evil_guy")
        second = dicts[1]
        self.assertEqual(second["name"], "peter")
        self.assertEqual(second["opponent"], "paul")
        third = dicts[2]
        self.assertEqual(third["name"], "michael_romeo")
        self.assertEqual(third["opponent"], "russell_allen")

    def test_translation(self):
        self.assertEquals(translate_move_to_indexes('20-14'), (19, 13))
        self.assertEquals(translate_move_to_indexes('21-off'), (20, 24))
        self.assertEquals(translate_move_to_indexes('bar-20'), (24, 19))

        self.assertEquals(translate_indexes_to_move(19, 13), "20-14")
        self.assertEquals(translate_indexes_to_move(19, 24), "20-off")
        self.assertEquals(translate_indexes_to_move(24, 19), "bar-20")


if __name__ == '__main__':
    unittest.main()
