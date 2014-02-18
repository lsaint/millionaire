# -*- coding: utf-8 -*-

from timer import Timer
from sender import Sender
from player import Player
import logic_pb2

class Room(Sender):

    def __init__(self, tsid, ssid):
        sender.__init__(self, tsid, ssid)
        self.timer = Timer()
        self.uid2player = {}
        self.status = Idle
        self.presenter = None


    def reset(self):
        self.timer.ReleaseTimer()
        self.timer = Timer()


    def OnLogin(self, ins):
        player = Player(ins.user)
        self.uid2player[ins.user.uid] = player
        rep = L2CLoginRep()
        rep.user = ins.user
        rep.ret = OK
        rep.status = self.status
        self.Randomcast(rep)


    def OnTimeSync(self, ins):
        pass


    def OnPing(self, ins):
        pass


    def OnNotifyMic1(self, ins):
        if ins.action == Up:
            player = self.uid2player.get(ins.user.uid)
            self.presenter = player


    def OnNextStep(self, ins):
        pass



