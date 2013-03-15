import threading
import time
from meowbg.core.board import BLACK, WHITE
from meowbg.core.bot import Bot
from meowbg.core.dice import FakeDice
from meowbg.core.events import MatchEvent, DiceEvent
from meowbg.core.messaging import broadcast
from meowbg.gui.guievents import (UndoAttemptEvent, MoveAttemptEvent,
                                  CommitAttemptEvent, RollAttemptEvent)
from meowbg.gui.main import BoardApp
from meowbg.network.connectionpool import DummyConnection, share_connection
from meowbg.network.translation import FIBSTranslator

APP = BoardApp()
parse = FIBSTranslator().parse_match


def test_hit():
    match = parse("board:player1:player2"
                  ":1"       # match length
                  ":0:0"     # score
                  ":-1"       # bar player 1
                  ":0:0:0:0:0:0:0:0:-1:-1:0:0:0:0:0:0:0:2:0:0:0:0:0:0" # board
                  ":0"       # bar player 2
                  ":1"       # turn
                  ":6:2:0:0" # dice
                  ":1"       # cube
                  ":1:1"     # may double
                  ":0:1:-1:0:25:0:0:0:0:2:0:0:0", # cruft
                  online=False)
    broadcast(MatchEvent(match))
    broadcast(DiceEvent(match.initial_dice))
    broadcast(MoveAttemptEvent(17, 11))
    broadcast(MoveAttemptEvent(11, 9))
    match.dice = FakeDice()
    match.dice.set_next_dice(4, 3)
    broadcast(CommitAttemptEvent(BLACK))

    time.sleep(2)
    broadcast(RollAttemptEvent(WHITE))
    broadcast(MoveAttemptEvent(-1, 3))
    broadcast(MoveAttemptEvent(-1, 2))
    broadcast(CommitAttemptEvent(WHITE))


def test_undo_after_hit():
    match = parse("board:player1:player2"
                  ":1"       # match length
                  ":0:0"     # score
                  ":-1"       # bar player 1
                  ":0:0:0:0:0:0:0:0:-1:-1:0:0:0:0:0:0:0:2:0:0:0:0:0:0" # board
                  ":0"       # bar player 2
                  ":1"       # turn
                  ":6:2:0:0" # dice
                  ":1"       # cube
                  ":1:1"     # may double
                  ":0:1:-1:0:25:0:0:0:0:2:0:0:0", # cruft
                  online=False)
    broadcast(MatchEvent(match))
    broadcast(DiceEvent(match.initial_dice))
    broadcast(MoveAttemptEvent(17, 11))
    broadcast(MoveAttemptEvent(11, 9))
    match.dice = FakeDice()
    match.dice.set_next_dice(4, 3)
    broadcast(CommitAttemptEvent(BLACK))

    time.sleep(2)
    broadcast(RollAttemptEvent(WHITE))
    broadcast(MoveAttemptEvent(-1, 3))
    broadcast(MoveAttemptEvent(-1, 2))
    broadcast(UndoAttemptEvent(WHITE))
    broadcast(UndoAttemptEvent(WHITE))
    broadcast(MoveAttemptEvent(-1, 3))
    broadcast(MoveAttemptEvent(-1, 2))
    broadcast(CommitAttemptEvent(WHITE))


def test_between_games():
    match = parse("board:player1:you"
                  ":3"       # match length
                  ":0:0"     # score
                  ":0"       # bar player 1
                  ":1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:-1" # board
                  ":0"       # bar player 2
                  ":-1"       # turn
                  ":6:2:0:0" # dice
                  ":1"       # cube
                  ":1:1"     # may double
                  ":0:1:-1:0:25:0:0:0:0:2:0:0:0", # cruft
                  online=False)
    match.register_player(Bot('Bottus', WHITE), WHITE)
    broadcast(MatchEvent(match))

def test_no_moves_possible():
    match = parse("board:player1:you"
                  ":3"       # match length
                  ":0:0"     # score
                  ":1"       # bar player 1
                  ":2:2:2:2:2:2:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:-1" # board
                  ":-1"       # bar player 2
                  ":-1"       # turn
                  ":6:6:0:0" # dice
                  ":1"       # cube
                  ":1:1"     # may double
                  ":0:1:-1:0:25:0:0:0:0:2:0:0:0", # cruft
                  online=False)
    match.register_player(Bot('Bottus', WHITE), WHITE)
    broadcast(MatchEvent(match))


def test_double():
    match = parse("board:player1:player2"
                  ":1"       # match length
                  ":0:0"     # score
                  ":0"       # bar player 1
                  ":1:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:0:-1" # board
                  ":0"       # bar player 2
                  ":-1"       # turn
                  ":6:2:0:0" # dice
                  ":1"       # cube
                  ":1:1"     # may double
                  ":0:1:-1:0:25:0:0:0:0:2:0:0:0", # cruft
                  online=False)
    broadcast(MatchEvent(match))


def execute_script():
    time.sleep(1)
    #test_hit()
    #test_undo_after_hit()
    #test_between_games()
    #test_new_game()
    #test_double()
    test_no_moves_possible()

if __name__ == '__main__':
    share_connection("Tigergammon", DummyConnection())
    action_thread = threading.Thread(target=execute_script)
    action_thread.start()
    APP.run()

