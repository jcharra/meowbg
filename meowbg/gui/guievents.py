
"""
Event classes that will be triggered by GUI interaction
and classes that are mostly GUI-related and hardly model-related.
"""



# A collection of 'attempt' events that result from a clicked
# button, not necessarily having an effect on the game.

class MoveAttemptEvent(object):
    def __init__(self, origin, target):
        self.origin, self.target = origin, target

    def __repr__(self):
        return "MoveAttemptEvent: %s->%s" % (self.origin, self.target)

class Attempt(object):
    """
    Abstract class representing an attempt to execute
    an action (to be defined by subclasses) for a
    given color.
    """
    def __init__(self, color=None):
        self.color = color

    def __repr__(self):
        return "%s by %s" % (self.__class__, self.color)

class RollAttemptEvent(Attempt):
    pass

class DoubleAttemptEvent(Attempt):
    pass

class CommitAttemptEvent(Attempt):
    pass

class UndoAttemptEvent(Attempt):
    pass

class ResignAttemptEvent(Attempt):
    pass

class NewMatchEvent(object):
    def __init__(self, match):
        self.match = match


# Several animation-related events

class AnimationStartedEvent(object):
    def __init__(self, moving_checker, target_spike, speedup=1):
        self.moving_checker = moving_checker
        self.target_spike = target_spike
        self.speedup = speedup

class AnimationFinishedEvent(object):
    pass

class HitEvent(object):
    def __init__(self, field_idx, hitting_color):
        self.field_idx, self.hitting_color = field_idx, hitting_color

class UnhitEvent(object):
    def __init__(self, field_idx, hit_color):
        self.field_idx, self.hit_color = field_idx, hit_color

# A pause event to insert breaks, e.g. in between subsequent animations

class PauseEvent(object):
    def __init__(self, ms):
        self.ms = ms

# Bring the match window into the foreground, i.e. focus it

class MatchFocusEvent(object):
    pass
