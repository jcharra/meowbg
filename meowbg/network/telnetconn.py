#!/usr/bin/env python

import os
import telnetlib
import logging
import time
import threading

logger = logging.getLogger("TelnetClient")
log_base = os.path.join(os.environ.get("MEOWBG_ROOT", "."), "logs")
networklog = os.path.join(log_base, "network.log")
logger.addHandler(logging.FileHandler(networklog))

logger.setLevel(logging.INFO)


class TelnetConnection(object):
    HOSTS = {'Tigergammon': ('tigergammon.com', 4321),
             'FIBS': ('fibs.com', 4321)}

    logger = logging.getLogger("Telnet")

    def __init__(self, host_key=None, username="", password=""):
        self.host, self.port = self.HOSTS[host_key] if host_key else self.HOSTS['Tigergammon']
        self.username, self.password = username or 'meowbg_joe', password or 'qwertz'
        self.tn_conn = None
        self.reading_thread = None
        self.alive = False

    def connect(self, callback_func):
        """
        Being logged in is currently considered part of the connection
        """
        logger.info("Establishing connection to %s:%s" % (self.host, self.port))
        self.tn_conn = telnetlib.Telnet(self.host, self.port, timeout=3)

        self.tn_conn.read_until('login: ')
        self.tn_conn.write("login meowBG 1008 %s %s\r\n" % (self.username, self.password))
        self.tn_conn.write("set boardstyle 3\r\n")
        self.tn_conn.write("toggle moreboards\r\n")

        self.callback = callback_func
        self.reading_thread = threading.Thread(target=self.read_forever)
        self.reading_thread.start()

    def read_forever(self):
        self.alive = True
        while self.alive:
            data = self.read()
            if data:
                self.callback(data)
            time.sleep(0.5)

    def read(self):
        try:
            text = unicode(self.tn_conn.read_very_eager(), errors='ignore')
            if text.strip():
                logger.log(logging.INFO, text)
            return text
        except Exception, msg:
            logger.info("Read response failed: %s" % msg)
            return ""

    def send(self, msg):
        msg = msg.encode('ascii')
        self.tn_conn.write(msg + "\r\n")

    def shutdown(self):
        self.alive = False
        self.tn_conn.close()


class Autoresponder(object):
    HOST, PORT, USER, PASSWORD = 'foo', 1, 'bla', 'blub'

    def __init__(self, host=None, port=None):
        self.host = self.port = None
        self.tn_conn = None
        self.file = open("telnet_complete_match.log", "r")
        logger.warn("Initialized")

    def read(self):
        buffer = ""
        while True:
            line = self.file.readline()
            buffer.append(line)
            if not line.strip():
                return buffer

    def write(self, msg):
        pass

    def send_msg(self, msg):
        pass

if __name__ == '__main__':
    tc = TelnetConnection()

    # Comment remains here in honour of Dr. Houseman
    # I'll sleep for some time to have a chance to get some asynchronous
    # messages from the server due to activities there;
    # this shows that I am collecting 'telnet-communication-data'
    time.sleep(10)

    print tc.tn_conn.read_very_eager()
    print 7, '+'*80

    tc.tn_conn.write('end\r\n')
    print tc.tn_conn.read_all()
