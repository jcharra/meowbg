

class MatchEvent(object):
    def __init__(self, match):
        self.match = match

class RollRequest(object):
    pass

class DiceEvent(object):
    def __init__(self, dice):
        self.dice = dice

    def __repr__(self):
        return "DiceEvent: %s" % self.dice

class CubeEvent(object):
    def __init__(self, color, cube_number):
        self.color, self.cube_number = color, cube_number

class RolloutEvent(object):
    def __init__(self, d1, d2):
        self.d1, self.d2 = d1, d2

class MoveEvent(object):
    def __init__(self, moves):
        """
        Contains a list  of 1-4 partial moves
        """
        self.moves = moves

    def __repr__(self):
        return " ".join(str(m) for m in self.moves)

class SingleMoveEvent(object):
    def __init__(self, move):
        self.move = move

class UndoMoveEvent(object):
    def __init__(self, move):
        self.move = move

class CommitEvent(object):
    def __init__(self, moves):
        self.moves = moves

class ResignEvent(object):
    def __init__(self, points):
        self.points = points

class AcceptEvent(object):
    def __init__(self, color):
        self.color = color

class RejectEvent(object):
    def __init__(self, color):
        self.color = color

class GameEndEvent(object):
    def __init__(self, winner, points):
        self.winner, self.points = winner, points

class MatchEndEvent(object):
    def __init__(self, winner, score):
        self.winner, self.score = winner, score

class CommandEvent(object):
    def __init__(self, command):
        self.command = command

# Events outside a match

class MessageEvent(object):
    def __init__(self, msg):
        self.msg = msg

class InvitationEvent(object):
    def __init__(self, player_name, length=0):
        self.player_name = player_name
        self.length = length

class PlayerStatusEvent(object):
    def __init__(self, status_dicts):
        """
        Receive a list of dictionaries indicating the
        statuses of 1..n players.
        """
        self.status_dicts = status_dicts

class LoginEvent(object):
    """
    Use this to require a user login - currently unused
    """

class ConnectionRequest(object):
    """
    This can be broadcasted to request a connection of a certain
    type, which is given as a key. Cf. the connectionpool module
    for further reference.
    """
    def __init__(self, key, callback):
        self.key, self.callback = key, callback