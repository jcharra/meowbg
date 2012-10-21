
import logging
logger = logging.getLogger("Move")

class PartialMove(object):
    def __init__(self, origin, target):
        self.origin = origin
        # keep inside the usual boundaries
        self.target = min(max(target, -1), 24)

    def __eq__(self, obj):
        try:
            return (self.origin == obj.origin
                    and self.target == obj.target)
        except AttributeError, msg:
            logger.warn("Inappropriate object passed for comparison: %s" % obj)
            return False

    def __hash__(self):
        return hash((self.origin, self.target))

    def __repr__(self):
        return "'%s/%s'" % (self.origin, self.target)
