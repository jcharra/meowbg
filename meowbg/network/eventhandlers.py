from collections import defaultdict
import re
import logging
import threading
import time
from meowbg.core.board import Board, BLACK, WHITE
from meowbg.core.match import Match
from meowbg.core.move import PartialMove
from meowbg.core.events import InvitationEvent, MoveEvent, MatchEvent, PlayerStatusEvent

logger = logging.getLogger("EventParser")
logger.addHandler(logging.StreamHandler())

def translate_move_to_indexes(move_str):
    origin, target = move_str.lower().split("-")
    if origin != 'bar':
        orig_idx = int(origin) - 1
    else:
        orig_idx = -1 if int(target) < 6 else 24

    if target != 'off':
        target_idx = int(target) - 1
    else:
        target_idx = 24 if int(origin) > 18 else -1

    return orig_idx, target_idx

def translate_indexes_to_move(orig_idx, target_idx):
    if orig_idx not in (-1, 24):
        origin = orig_idx + 1
    else:
        origin = 'bar'

    if target_idx not in (-1, 24):
        target = target_idx + 1
    else:
        target = 'off'

    return "%s-%s" % (origin, target)

class GameEventHandler(object):
    """
    Abstract base class for game event handlers.
    """
    def __init__(self, opponent_interface):
        self.opponent_interface = opponent_interface

    def handle(self, event):
        """
        Handle incoming events
        """
        raise NotImplementedError

    def connect(self):
        """
        Connect this handler to its event source, which will make
        calls to the 'notify' method.
        """
        raise NotImplementedError

    def send_raw(self, text):
        self.opponent_interface.send_msg(text)


class AIEventHandler(GameEventHandler):
    """
    An event handler for responses from an AI.
    Will just pass any incoming events through to
    a connected AI instance.
    """

    def __init__(self, opponent_interface):
        GameEventHandler.__init__(self, opponent_interface)

    def connect(self):
        pass


class FIBSEventHandler(GameEventHandler):
    """
    A class for parsing Telnet output complying with the
    format given at http://www.fibs.com/fibs_interface.html
    """

    PLAYER_STATUS_EVENT = 5

    def __init__(self, opponent_interface):
        GameEventHandler.__init__(self, opponent_interface=opponent_interface)
        self.listening = False

    def connect(self):
        """
        Gives the parser a connection to periodically ask for
        new input to parse. Starts a separate thread for this.
        """
        self.listening = True
        self.read_thread = threading.Thread(target=self.read_data)
        self.read_thread.start()

    def read_data(self):
        while self.opponent_interface and self.listening:
            if self.opponent_interface.connected:
                data = self.opponent_interface.read()
                events = self.parse_events(data)
                for e in events:
                    self.notify(e)

            time.sleep(1)

    def send_raw(self, text):
        if self.listening:
            GameEventHandler.send_raw(self, text)

    def handle(self, event):
        """
        TODO: Translate the various kinds of events to FIBS messages and send them.
        """
        logger.info("I just received an event %s" % event)

    def parse_events(self, text):
        lines = filter(bool, [li.strip(" >") for li in text.split("\r\n")])
        found_events = []
        multiline_buffer = []

        for line in lines:
            if line.startswith("board:"):
                match = self.parse_match(line)
                found_events.append(MatchEvent(match))
            if line.startswith("5 "):
                multiline_buffer.append(line)
                continue
            elif line.startswith("6"):
                if not multiline_buffer:
                    logger.info("Orphaned '6'")
                    continue

                dicts = []
                for l in multiline_buffer:
                    dicts.append(self.parse_line_to_args(l, type=self.PLAYER_STATUS_EVENT))
                multiline_buffer = []
                found_events.append(PlayerStatusEvent(status_dicts=dicts))
            elif line.startswith("7 "):
                # Player logs in
                pass
            elif line.startswith("8 "):
                # Player logs out
                pass
            elif line.startswith("9 "):
                # from time message
                pass
            elif line.startswith("10 "):
                # message delivered
                pass
            elif line.startswith("11 "):
                # message saved
                pass
            elif line.startswith("12 "):
                # Says
                pass
            elif line.startswith("13 "):
                # player shouts
                pass
            elif line.startswith("14 "):
                # whispers
                pass
            elif line.startswith("15 "):
                # kibitzes
                pass
            elif line.startswith("16 "):
                # You say
                pass
            elif line.startswith("17 "):
                # you shout
                pass
            elif line.startswith("18 "):
                # you whisper
                pass
            elif line.startswith("19 "):
                # you kibitz
                pass
            elif re.search("^[a-zA-Z0-9_]+ moves ", line):

                # move event
                moves_raw = line.split("moves ")[1]
                moves = re.findall("\S+-\S+", moves_raw)
                partial_moves = []
                for m in moves:
                    origin, target = translate_move_to_indexes(m)
                    # TODO: make PartialMove class be color-independent
                    partial_moves.append(PartialMove(origin, target))
                found_events.append(MoveEvent(partial_moves))

            elif line.find(" wants to play ") != -1:
                if "unlimited match" in line:
                    args = re.search("(?P<user>\S+) wants to play an unlimited point match with you", line).groupdict()
                    found_events.append(InvitationEvent(player_name=args['user']))
                else:
                    args = re.search("(?P<user>\S+) wants to play a (?P<length>\d+) point match with you", line).groupdict()
                    found_events.append(InvitationEvent(player_name=args['user'], length=args['length']))
                logger.warn("Invite event: Got args %s" % args)
            elif line.find(" wants to resume ") != -1:
                # user wants to resume a saved match with you.
                args = re.search("(?P<user>\S+) wants to resume a saved match with you", line).groupdict()
                found_events.append(InvitationEvent(player_name=args['user']))
            else:
                logger.warn("Not parseable: '%s'" % line)

        for e in found_events:
            logger.warn("Found event %s with dict %s" % (e, e.__dict__))

        return found_events

    def parse_match(self, match_str):
        """
        Parse a string which represents a match strictly corresponding to
        the 'boardstyle 3' type described in detail here:
        http://www.fibs.com/fibs_interface.html#board_state
        """

        match = Match()

        parts = match_str.split(":")
        if len(parts) != 53:
            self.logger.error("Illegal board state: %s" % match_str)
            return

        match.player_names = parts[1], parts[2]

        parts[3:] = map(int, parts[3:])

        match.length = parts[3]
        match.score = parts[4], parts[5]
        board_str = parts[6:32]

        if parts[32] > 0:
            match.turn = BLACK
        elif parts[32] < 0:
            match.turn = WHITE
        else:
            match.turn = None

        match.players_dice = list(parts[33:35])
        match.players_remaining_dice = list(match.players_dice)
        if match.players_dice[0] == match.players_dice[1]:
            match.players_remaining_dice.extend(match.players_dice)
            match.players_dice.extend(match.players_dice)

        match.opponents_dice = parts[35], parts[36]
        match.cube = parts[37]
        match.player_may_double = parts[38]
        match.opponent_may_double = parts[39]
        match.was_doubled = parts[40]
        match.players_color = BLACK if parts[41] == 1 else WHITE
        match.players_direction = parts[42]
        match.move_possibilities = parts[49]

        on_field, on_bar = self.parse_board_str(board_str)
        match.board = Board(on_field=on_field, on_bar=on_bar)

        return match

    def parse_board_str(self, input_list):
        """
        Expects a list or tuple of length 26, i.e. only the
        checkers on the board and on the bar in the FIBS string.
        """

        checkers_on_bar = []
        on_bar = input_list[0], input_list[25]
        for hit_checker in on_bar:
            color = WHITE if hit_checker < 0 else BLACK
            checkers_on_bar.extend([color] * abs(hit_checker))

        checkers_on_field = defaultdict(list)
        for idx, val in enumerate(input_list[1:25]):
            color = WHITE if val < 0 else BLACK
            checkers_on_field[idx].extend([color] * abs(val))

        return checkers_on_field, checkers_on_bar


    def parse_line_to_args(self, line, type):
        """
        Universal parsing method, accepting a line and an event type.
        """
        if type == self.PLAYER_STATUS_EVENT:
            match = re.search(("5 (?P<name>\S+) (?P<opponent>\S+) (?P<watching>\S+) (?P<ready>\S+) "
                               "(?P<away>\S+) (?P<rating>\S+) (?P<experience>\S+) (?P<idle>\S+) (?P<login>\S+) "
                               "(?P<hostname>\S+) (?P<client>\S+) (?P<email>\S+)"), line)
            if match:
                return match.groupdict()
            else:
                logger.error("Malformed status event: %s" % line)
        else:
            logger.error("Cannot parse line of type %s" % type)

        # Indicates failure
        return {}
