class NewMatchEvent(object):
    def __init__(self, length):
        self.length = length

class MoveAttempt(object):
    def __init__(self, origin, target):
        self.origin, self.target = origin, target

    def __repr__(self):
        return "MoveEvent: %s->%s" % (self.origin, self.target)

class MoveAnimationEvent(object):
    def __init__(self, moving_checker, target_pos):
        self.moving_checker, self.target_pos = moving_checker, target_pos

class AnimationStartedEvent(object):
    def __init__(self, data):
        self.data = data

class AnimationFinishedEvent(object):
    def __init__(self, data):
        self.data = data

class HitEvent(object):
    def __init__(self, field_idx, hitting_color):
        self.field_idx, self.hitting_color = field_idx, hitting_color