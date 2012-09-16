class NewMatchEvent(object):
    def __init__(self, length):
        self.length = length

class MoveAttempt(object):
    def __init__(self, origin, target):
        self.origin, self.target = origin, target

    def __repr__(self):
        return "MoveEvent: %s->%s" % (self.origin, self.target)

class AnimationStartedEvent(object):
    def __init__(self, data):
        self.data = data

class AnimationFinishedEvent(object):
    def __init__(self, data):
        self.data = data

