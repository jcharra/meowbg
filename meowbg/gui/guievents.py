class NewMatchEvent(object):
    def __init__(self, length):
        self.length = length

class MoveAttempt(object):
    def __init__(self, origin, target):
        self.origin, self.target = origin, target

class AnimationFinishedEvent(object):
    pass
