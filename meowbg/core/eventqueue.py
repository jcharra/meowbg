
import logging
from collections import deque
from kivy.clock import Clock

logger = logging.getLogger("EventQueue")
logger.addHandler(logging.StreamHandler())

class SynchronizedTaskQueue(object):
    def __init__(self):
        self.queue = deque([])
        self.running_func = None
        self.next_event = None

    def synced_call(self, func):
        def func_call(e):
            self.queue.append((func, e))
            self.try_next()

        return func_call

    def release_and_proceed(self):
        self.running_func = None
        self.try_next()

    def try_next(self):
        if self.running_func:
            logger.warn("Queue is currently blocked by %s" % self.running_func)
            return

        if self.queue:
            self.running_func, self.next_event = self.queue.popleft()
            Clock.schedule_once(lambda e: self.do_next(), 0.1)

    def do_next(self):
        logger.warn("Now executing %s" % self.running_func)
        self.running_func(self.next_event, self.release_and_proceed)

GlobalTaskQueue = SynchronizedTaskQueue()