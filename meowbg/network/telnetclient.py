#!/usr/bin/env python

import telnetlib
import logging
import time

logger = logging.getLogger("TelnetClient")
logger.addHandler(logging.FileHandler('telnet.log'))
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

class TelnetClient(object):
    HOSTS = {'Tigergammon': ('tigergammon.dyndns-home.com', 4321),
             'FIBS': ('fibs.com', 4321)}

    logger = logging.getLogger("Telnet")

    def __init__(self, host_key=None, username="", password=""):
        self.host, self.port = self.HOSTS[host_key] if host_key else self.HOSTS['Tigergammon']
        #self.username = (username or u'_joc_').encode('utf-8')
        #self.password = (password or u'qwertz').encode('utf-8')
        self.username, self.password = 'meowbg_joe', 'qwertz'
        self.tn_conn = None
        self.connected = False
        self._establish_connection()

    def _establish_connection(self):
        """
        Being logged in is currently considered part of the connection
        """
        logger.info("Establishing connection to %s:%s" % (self.host, self.port))
        if not self.tn_conn:
            self.tn_conn = telnetlib.Telnet(self.host, self.port, timeout=3)
        else:
            self.tn_conn.close()
            self.tn_conn.open(self.host, self.port, timeout=3)

        self.tn_conn.read_until('login: ')
        self.tn_conn.write("login meowBG 1008 %s %s\r\n" % (self.username, self.password))
        self.tn_conn.write("set boardstyle 3\r\n")
        self.connected = True

    def read(self):
        try:
            text = unicode(self.tn_conn.read_very_eager(), errors='ignore')
            if text.strip():
                logger.log(logging.INFO, text)
            return text
        except Exception, msg:
            logger.info("Read response failed: %s" % msg)
            self._establish_connection()
            return ""

    def write(self, msg):
        self.tn_conn.write(msg)

    def send_msg(self, msg):
        msg = msg.encode('ascii')
        self.tn_conn.write(msg + "\r\n")
        return self.read()


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
    tc = TelnetClient()

    # Comment remains here in honour of Dr. Houseman
    # I'll sleep for some time to have a chance to get some asynchronous
    # messages from the server due to activities there;
    # this shows that I am collecting 'telnet-communication-data'
    time.sleep(10)

    print tc.tn_conn.read_very_eager()
    print 7, '+'*80

    tc.tn_conn.write('end\r\n')
    print tc.tn_conn.read_all()
