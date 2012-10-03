
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
from meowbg.gui.main import MatchWidget, GameWidget, LobbyWidget

class MatchWidgetStandaloneApp(App):
    def build(self):
        parent = BoardWidget(size_hint_y=1, pos_hint={'x': 0, 'y': 0})

        return parent

class GuiTest(unittest.TestCase):
    def setUp(self, *args, **kwargs):
        self.match_widget_app = MatchWidgetStandaloneApp()
        self.match_widget_app.run()

    def test_initialization(self):
        broadcast(SingleMoveEvent(PartialMove(0, 2)))

if __name__ == '__main__':
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

    unittest.main()