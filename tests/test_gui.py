
import unittest
from kivy.app import App
from kivy.factory import Factory
from meowbg.core.board import WHITE, BLACK
from meowbg.core.events import SingleMoveEvent
from meowbg.core.match import Match
from meowbg.core.messaging import broadcast
from meowbg.core.move import PartialMove
from meowbg.core.player import HumanPlayer
from meowbg.gui.basicparts import IndexRow, SpikePanel, BearoffPanel, BarPanel, Spike, ButtonPanel
from meowbg.gui.boardwidget import BoardWidget
from meowbg.gui.main import MatchWidget, GameWidget, LobbyWidget, BoardApp


class MatchWidgetStandaloneApp(App):
    def __init__(self, *args, **kwargs):
        App.__init__(self, **kwargs)
        self.board = BoardWidget(size_hint_y=1, pos_hint={'x': 0, 'y': 0})

    def build(self):
        return self.board
APP = MatchWidgetStandaloneApp()

class GuiTest(unittest.TestCase):
    def test_initialization(self):
        broadcast(NewM(PartialMove(0, 2)))
        self.assertEqual(APP.board, "")


Factory.register("LobbyWidget", LobbyWidget)
Factory.register("MatchWidget", MatchWidget)
Factory.register("GameWidget", GameWidget)
Factory.register("ButtonPanel", ButtonPanel)
Factory.register("BoardWidget", BoardWidget)
Factory.register("Spike", Spike)
Factory.register("BarPanel", BarPanel)
Factory.register("BearoffPanel", BearoffPanel)
Factory.register("SpikePanel", SpikePanel)
Factory.register("IndexRow", IndexRow)

if __name__ == '__main__':
    APP.run()
    unittest.main()