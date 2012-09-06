#!/usr/bin/python

import os, sys

BASE = os.path.dirname(__file__)
sys.path.insert(0, BASE)

from meowbg.gui.main import BoardApp

BoardApp().run()