from meowbg.core.events import ConnectionRequest
from meowbg.core.messaging import register

connections = {}

def share_connection(key, conn):
    connections[key] = conn

def get_connection(key):
    return connections.get(key)


class DummyConnection(object):
    def send(self, args):
        pass
