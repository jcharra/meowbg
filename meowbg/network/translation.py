from collections import defaultdict
import re
import logging
from meowbg.core.board import Board, BLACK, WHITE
from meowbg.core.match import OnlineMatch, OfflineMatch
from meowbg.core.events import (IncomingInvitationEvent, MoveEvent, MatchEvent, PlayerStatusEvent, DiceEvent,
                                RollRequest, AcceptEvent, RejectEvent, MatchEndEvent, AcceptJoinEvent,
                                ResignOfferEvent, JoinChallengeEvent, OpponentJoinedEvent,
                                GameEndEvent, IncompleteInvitationEvent, MessageEvent)
from meowbg.core.player import HumanPlayer, get_or_create_player_proxy
from meowbg.gui.guievents import DoubleAttemptEvent, MoveAttemptEvent

logger = logging.getLogger("EventParser")
logger.addHandler(logging.FileHandler("parsing.log"))
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


class FIBSTranslator(object):
    """
    A class for parsing Telnet output complying with the
    format given at http://www.fibs.com/fibs_interface.html
    as well as translating meowBG events into FIBS events.
    """

    PLAYER_STATUS_EVENT = 5

    def __init__(self):
        self.current_match = None

    def encode_refresh(self):
        return "board"

    def encode(self, event):
        """
        TODO: Translate the various kinds of events to FIBS messages.
        """
        logger.warn("I just received an event %s" % event)
        if isinstance(event, MoveEvent):
            return "move " + " ".join(translate_indexes_to_move(m.origin, m.target) for m in event.moves)
        elif isinstance(event, RollRequest):
            return "roll"
        elif isinstance(event, DoubleAttemptEvent):
            return "double"
        elif isinstance(event, AcceptEvent):
            return "accept"
        elif isinstance(event, RejectEvent):
            return "reject"
        elif isinstance(event, AcceptJoinEvent):
            return "join"
        elif isinstance(event, ResignOfferEvent):
            resign_choice = {1: 'n', 2: 'g', 3: 'b'}
            return "resign %s" % resign_choice.get(event.points, 'n')

        logger.error("Cannot encode event type %s" % event)
        return ""

    def parse_events(self, text):
        lines = filter(bool, [str(li.strip(" >")) for li in text.split("\r\n")])
        found_events = []
        multiline_buffer = []

        for line in lines:
            if line.startswith("board:"):
            #if re.search("board:\S+:\S+:([-\d]+){50}", line):
                match = self.parse_match(line)
                found_events.append(MatchEvent(match))
                self.current_match = match
            elif line.startswith("5 "):
                multiline_buffer.append(line)
                continue
            elif line.startswith("6"):
                if not multiline_buffer:
                    logger.info("Orphaned '6'")
                    continue

                dicts = []
                for l in multiline_buffer:
                    dicts.append(self.parse_line_to_args(l, line_type=self.PLAYER_STATUS_EVENT))
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
                found_events.append(MessageEvent(line.split(" ", 1)[1]))
            elif line.startswith("13 "):
                # player shouts
                found_events.append(MessageEvent(line.split(" ", 1)[1]))
            elif line.startswith("14 "):
                # whispers
                found_events.append(MessageEvent(line.split(" ", 1)[1]))
            elif line.startswith("15 "):
                # kibitzes
                pass
            elif line.startswith("16 "):
                # You say
                found_events.append(MessageEvent("YOU SAY: " + line.split(" ", 1)[1]))
            elif line.startswith("17 "):
                # You shout
                found_events.append(MessageEvent("YOU SHOUT: " + line.split(" ", 1)[1]))
            elif line.startswith("18 "):
                # you whisper
                found_events.append(MessageEvent("You whisper: " + line.split(" ", 1)[1]))
            elif line.startswith("19 "):
                # you kibitz
                pass
            elif re.search("^\S+ rolls? [1-6] and [1-6]", line):
                player_name, die1, die2 = re.search("^(\S+) rolls? ([1-6]) and ([1-6])", line).groups()
                found_events.append(DiceEvent(map(int, [die1, die2])))
            elif re.search("^[a-zA-Z0-9_]+ moves ", line):

                if not self.current_match:
                    logger.error("Found a move event without having a match in my hands ...")
                    return

                # move event
                pname = re.search("^([a-zA-Z0-9_]+) moves ", line).groups()[0]
                pcol = self.current_match.get_players_color(pname)

                if not pcol:
                    logger.error("Player %s does not participate in match %s" % (pname, self.current_match))
                    return

                moves_raw = line.split("moves ")[1]
                moves = re.findall("\S+-\S+", moves_raw)
                for m in moves:
                    origin, target = translate_move_to_indexes(m)
                    found_events.append(MoveAttemptEvent(origin, target))

            elif line.find(" wants to play ") != -1:
                if "unlimited match" in line:
                    args = re.search("(?P<user>\S+) wants to play an unlimited point match with you", line).groupdict()
                    found_events.append(IncomingInvitationEvent(player_name=args['user']))
                else:
                    args = re.search("(?P<user>\S+) wants to play a (?P<length>\d+) point match with you", line).groupdict()
                    found_events.append(IncomingInvitationEvent(player_name=args['user'], length=args['length']))
                logger.warn("Invite event: Got args %s" % args)
            elif line.find(" wants to resume ") != -1:
                # user wants to resume a saved match with you.
                args = re.search("(?P<user>\S+) wants to resume a saved match with you", line).groupdict()
                found_events.append(IncomingInvitationEvent(player_name=args['user']))
            elif re.search("\S+ has doubled you. Type 'accept' or 'reject'.", line):
                if not self.current_match:
                    continue
                pname = re.search("(\S+) has doubled you", line).groups()[0]
                color = self.current_match.get_players_color(pname)

                if not color:
                    logger.error("Doubling by player %s found, who does not participate in match" % pname)

                found_events.append(DoubleAttemptEvent(color))
            elif re.search("\S+ doubles. Type 'accept' or 'reject'.", line):
                if not self.current_match:
                    continue
                pname = re.search("(\S+) doubles. Type", line).groups()[0]
                color = self.current_match.get_players_color(pname)

                if not color:
                    logger.error("Doubling by player %s found, who does not participate in match" % pname)

                found_events.append(DoubleAttemptEvent(color))
            elif re.search("There's no saved match with \S+. Please give a match length.", line):
                pname = re.search("There's no saved match with (\S+). Please give a match length.", line).groups()[0]
                found_events.append(IncompleteInvitationEvent(pname))
            elif re.search("(\S+) (accepts and)? wins? (\d+) points", line):
                if not self.current_match:
                    continue
                pname, _, points = re.search("(\S+) (accepts and)? wins? (\d+) points", line).groups()

                if not self.current_match.get_players_color(pname):
                    logger.info("Dismissing notification about %s" % pname)
                    continue

                found_events.append(GameEndEvent(pname, points))
            elif line.find(" has joined you. Your running match was loaded.") != -1:
                found_events.append(OpponentJoinedEvent())
            elif line.find("Type 'join' if you want to play the next game") != -1:
                if self.current_match:
                    found_events.append(JoinChallengeEvent(self.current_match))
            elif re.match("\S+ wins? the \d+ point match \d+-\d+", line):
                winner, score1, score2 = re.search("(\S+) wins? the \d+ point match (\d+)-(\d+)", line).groups()
                pcol = self.current_match.get_players_color(winner)

                if not pcol:
                    logger.info("Player %s does not participate in match %s" % (winner, self.current_match))
                    return

                score = {BLACK: score1, WHITE: score2}
                found_events.append(MatchEndEvent(winner, score))
            else:
                logger.warn("Not parseable: %r" % line)

        for e in found_events:
            pass
            #logger.warn("Found event %s with dict %s" % (e, e.__dict__))

        return found_events

    def parse_match(self, match_str, online=True):
        """
        Parse a string which represents a match strictly corresponding to
        the 'boardstyle 3' type described in detail here:
        http://www.fibs.com/fibs_interface.html#board_state
        """

        match = OnlineMatch() if online else OfflineMatch()

        parts = match_str.split(":")
        if len(parts) != 53:
            logger.error("Illegal board state: %s" % match_str)
            return

        your_color, opponents_color = (WHITE, BLACK) if parts[41] == -1 else (BLACK, WHITE)
        # TODO: simplify
        if parts[1].lower() == "you":
            match.register_player(HumanPlayer(parts[1], your_color), your_color)
            player_proxy = get_or_create_player_proxy(parts[2], opponents_color, self)
            match.register_player(player_proxy, opponents_color)
        else:
            logger.error("Kiebitzing not supported yet")
            match.register_player(HumanPlayer(parts[1], your_color), your_color)
            match.register_player(HumanPlayer(parts[2], opponents_color), opponents_color)

        parts[3:] = map(int, parts[3:])

        match.length = parts[3]
        match.score = {BLACK: parts[4], WHITE: parts[5]}
        board_str = parts[6:32]

        if parts[32] > 0:
            match.color_to_move_next = BLACK
        elif parts[32] < 0:
            match.color_to_move_next = WHITE
        else:
            match.color_to_move_next = None

        # Pick the dice that contain non-zero values
        whites_dice = parts[33], parts[34]
        blacks_dice = parts[35], parts[36]
        if whites_dice[0]:
            match.initial_dice = list(whites_dice)
        elif blacks_dice[0]:
            match.initial_dice = list(blacks_dice)
        else:
            # no dice given, so don't set anything
            pass

        match.remaining_dice = list(match.initial_dice)
        if match.initial_dice and match.initial_dice[0] == match.initial_dice[1]:
            match.initial_dice.extend(match.initial_dice)
            match.remaining_dice.extend(match.remaining_dice)

        match.cube = parts[37]
        match.may_double = {BLACK: parts[38], WHITE: parts[39]}

        just_doubled = parts[40]
        if just_doubled:
            match.open_cube_challenge_from_color = opponents_color

        on_field, on_bar = self.parse_board_str(board_str)
        match.board = Board(on_field=on_field, on_bar=on_bar)
        if match.initial_dice:
            match.board.store_initial_possibilities(match.initial_dice, match.color_to_move_next)

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

    def parse_line_to_args(self, line, line_type):
        """
        Universal parsing method, accepting a line and an event type.
        """
        if line_type == self.PLAYER_STATUS_EVENT:
            match = re.search(("5 (?P<name>\S+) (?P<opponent>\S+) (?P<watching>\S+) (?P<ready>\S+) "
                               "(?P<away>\S+) (?P<rating>\S+) (?P<experience>\S+) (?P<idle>\S+) (?P<login>\S+) "
                               "(?P<hostname>\S+) (?P<client>\S+) (?P<email>\S+)"), line)
            if match:
                return match.groupdict()
            else:
                logger.error("Malformed status event: %s" % line)
        else:
            logger.error("Cannot parse line of type %s" % line_type)

        # Indicates failure
        return {}

