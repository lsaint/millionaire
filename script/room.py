
# -*- coding: utf-8 -*-

from timer import Timer
from sender import Sender

class Room(Sender):

    def __init__(self, tsid, ssid):
        sender.__init__(self, tsid, ssid)
        self.timer = Timer()


    def reset(self):
        self.timer.ReleaseTimer()
        self.timer = Timer()



