
from collections import deque
import logging

logger = logging.getLogger("EventQueue")
logger.addHandler(logging.StreamHandler())

class SynchronizedTaskQueue(object):
    def __init__(self):
        self.queue = deque([])
        self.processing = False

    def synced_call(self, func):
        def func_call(e):
            if self.processing:
                logger.warn("Queue is blocked ... deferring the call of %s with event %s"
                            % (func, e))
                self.queue.append((func, e))
            else:
                logger.warn("Queue is FREE ... immediately calling %s with event %s"
                            % (func, e))
                func(e, self.next)
        return func_call

    def next(self):
        logger.warn("Queue is now idle")
        self.processing = False
        if self.queue:
            func, event = self.queue.popleft()
            self.processing = True
            func(event, self.next)

GlobalTaskQueue = SynchronizedTaskQueue()