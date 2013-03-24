from meowbg.core.events import ConnectionRequest
from meowbg.core.messaging import register

connections = {}


def share_connection(key, conn):
    connections[key] = conn


def get_connection(key=None):
    return connections.get(key) if key else connections.values()[0]


class DummyConnection(object):
    def send(self, args):
        pass
