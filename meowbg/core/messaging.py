import os
import logging

logger = logging.getLogger("Messaging")
log_base = os.path.join(os.environ["MEOWBG_ROOT"], "logs")
eventlog = os.path.join(log_base, "events.log")
logger.addHandler(logging.FileHandler(eventlog))

# mapping from object instances to event classes
SUBSCRIPTIONS = {}


def register(callback, event_class):
    SUBSCRIPTIONS.setdefault(event_class, []).append(callback)
    #logger.warn("New registration. Now having {} subscriptions: {}".format(len(SUBSCRIPTIONS),
    #                                                                       "\n\t".join("{}=>{}".format(e, rec) for e, rec in SUBSCRIPTIONS.iteritems())))


def unregister(callback, event_class):
    if callback in SUBSCRIPTIONS[event_class]:
        SUBSCRIPTIONS[event_class].remove(callback)


def broadcast(event):
    logger.warn("***** EVENT: %s" % event)
    subscribers = SUBSCRIPTIONS.get(event.__class__, [])
    for s in subscribers:
        logger.warn("Sending %s to %s" % (event, s))
        s(event)
