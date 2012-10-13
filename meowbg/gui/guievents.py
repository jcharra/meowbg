class NewMatchEvent(object):
    def __init__(self, match):
        self.match = match

class MoveAttempt(object):
    def __init__(self, origin, target):
        self.origin, self.target = origin, target

    def __repr__(self):
        return "MoveEvent: %s->%s" % (self.origin, self.target)

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