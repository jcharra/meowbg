#!/usr/bin/python

import os, sys

BASE = os.path.dirname(__file__)
sys.path.insert(0, BASE)

os.environ["MEOWBG_ROOT"] = BASE

from meowbg.gui.main import BoardApp

BoardApp().run()