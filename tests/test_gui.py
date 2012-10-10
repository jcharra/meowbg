import threading
import time
from meowbg.core.messaging import broadcast
from meowbg.gui.guievents import NewMatchEvent
from meowbg.gui.main import MatchWidget, GameWidget, LobbyWidget, BoardApp

APP = BoardApp()

def initialize(match_len):
    broadcast(NewMatchEvent(match_len))

def execute_script():
    time.sleep(2)
    initialize(1)

if __name__ == '__main__':
    action_thread = threading.Thread(target=execute_script)
    action_thread.start()
    APP.run()

