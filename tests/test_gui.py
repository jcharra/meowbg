import threading
import time
from meowbg.core.board import BLACK, WHITE
from meowbg.core.dice import FakeDice
from meowbg.core.events import MatchEvent, SingleMoveEvent, DiceEvent, CommitAttemptEvent
from meowbg.core.match import Match
from meowbg.core.messaging import broadcast
from meowbg.core.move import PartialMove
from meowbg.core.player import HumanPlayer
from meowbg.gui.guievents import NewMatchEvent, MoveAttempt
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
                  ":0:1:-1:0:25:0:0:0:0:2:0:0:0" # cruft
    )
    broadcast(MatchEvent(match))
    broadcast(DiceEvent(match.initial_dice))
    broadcast(MoveAttempt(17, 11))
    broadcast(MoveAttempt(11, 9))
    match.dice = FakeDice()
    match.dice.set_next_dice(4, 3)
    broadcast(CommitAttemptEvent())

    time.sleep(3)
    broadcast(DiceEvent(match.initial_dice))
    broadcast(MoveAttempt(-1, 3))
    broadcast(MoveAttempt(-1, 2))
    broadcast(CommitAttemptEvent())

def execute_script():
    time.sleep(1)
    test_hit()
    time.sleep(1)
    #test_new_game()

if __name__ == '__main__':
    share_connection("Tigergammon", DummyConnection())
    action_thread = threading.Thread(target=execute_script)
    action_thread.start()
    APP.run()

