import threading
import time
from meowbg.core.board import BLACK, WHITE
from meowbg.core.events import MatchEvent, SingleMoveEvent, DiceEvent, CommitEvent
from meowbg.core.match import Match
from meowbg.core.messaging import broadcast
from meowbg.core.move import PartialMove
from meowbg.core.player import HumanPlayer
from meowbg.gui.guievents import NewMatchEvent, MoveAttempt
from meowbg.gui.main import MatchWidget, GameWidget, LobbyWidget, BoardApp
from meowbg.network.translation import FIBSTranslator

APP = BoardApp()
MATCH = Match()
parse = FIBSTranslator().parse_match

def test_hit():
    match = parse("board:player1:player2"
                  ":1"       # match length
                  ":0:0"     # score
                  ":0"       # bar player 1
                  ":0:0:0:0:0:0:0:0:-1:-1:0:0:0:0:0:0:0:2:0:0:0:0:0:0" # board
                  ":0"       # bar player 2
                  ":1"       # turn
                  ":6:2:0:0" # dice
                  ":1"       # cube
                  ":1:1"     # may double
                  ":0:1:-1:0:25:0:0:0:0:2:0:0:0" # cruft
    )
    broadcast(MatchEvent(match))
    broadcast(DiceEvent(match.initial_dice, BLACK))
    broadcast(MoveAttempt(17, 11))
    broadcast(MoveAttempt(11, 9))
    broadcast(CommitEvent(BLACK))

def execute_script():
    time.sleep(1)
    MATCH.length = 1
    broadcast(NewMatchEvent(MATCH))
    time.sleep(1)
    test_hit()


if __name__ == '__main__':
    action_thread = threading.Thread(target=execute_script)
    action_thread.start()
    APP.run()

