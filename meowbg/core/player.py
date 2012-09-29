from meowbg.core.events import MatchEvent
from meowbg.core.messaging import register, unregister

class AbstractPlayer(object):
    def __init__(self, name, color):
        self.name, self.color = name, color
        register(self.react, MatchEvent)

    def exit(self):
        unregister(self.react, MatchEvent)

    def react(self, match_event):
        raise NotImplemented


class HumanPlayer(AbstractPlayer):
    def react(self, match_event):
        pass


class OnlinePlayer(AbstractPlayer):
    def __init__(self, name, color, connection, event_translator):
        AbstractPlayer.__init__(self, name, color)
        self.connection = connection
        self.event_translator = event_translator

    def react(self, match_event):
        self.event_translator.translate(match_event)
