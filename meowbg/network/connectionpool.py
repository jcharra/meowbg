from meowbg.core.events import ConnectionRequest
from meowbg.core.messaging import register

class ConnectionPool(object):
    def __init__(self):
        self.connections = {}
        register(self.respond, ConnectionRequest)

    def share_connection(self, key, conn):
        self.connections[key] = conn

    def respond(self, req_event):
        req_event.callback(self.connections.get(req_event.key))