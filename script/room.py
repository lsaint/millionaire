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
        self.presenter = None

        self.idle_state = IdleState(self)
        self.ready_state = ReadyState(self)
        self.timing_state = TimingState(self)
        self.timeup_state = TimeupState(self)
        self.statistics_state = StatisticsState(self)
        self.answer_state = AnswerState(self)
        self.announce_state = AnnounceState(self)
        self.award_state = AwardState(self)
        self.ending_state = EndingState(self)
        self.state = self.idle_state


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




#
class IdleState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.state = self.room.ready_state


#
class ReadyState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.state = self.room.timing_state


#
class TimingState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.state = self.room.timing_state


#
class TimeupState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.state = self.room.statistics_state


#
class StatisticsState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.state = self.room.answer_state


#
class AnswerState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.state = self.room.announce_state


#
class AnnounceState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.state = self.room.award_state


#
class AwardState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.state = self.room.ending_state


#
class EndingState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.state = self.room.idle_state


