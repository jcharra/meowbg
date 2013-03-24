import logging
logger = logging.getLogger("Messaging")
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler("events.log"))

# mapping from object instances to event classes
SUBSCRIPTIONS = {}


def register(callback, event_class):
    SUBSCRIPTIONS.setdefault(event_class, []).append(callback)


def unregister(callback, event_class):
    if callback in SUBSCRIPTIONS[event_class]:
        SUBSCRIPTIONS[event_class].remove(callback)


def broadcast(event):
    logger.warn("***** EVENT: %s" % event)
    subscribers = SUBSCRIPTIONS.get(event.__class__, [])
    for s in subscribers:
        #logger.warn("Sending %s to %s" % (event, s))
        s(event)
