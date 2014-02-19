# -*- coding: utf-8 -*-

from timer import Timer
from sender import Sender
from player import Player
from award import AwardChecker
from match import g_match_mgr
from logic_pb2 import *



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


    def setState(self, state):
        self.state = state


    def reset(self):
        self.timer.ReleaseTimer()
        self.timer = Timer()
        self.match = None
        self.achecker = None
        self.qpackage = QuesionPackage()


    def OnMatchInfo(self, ins):
        print "OnMatchInfo"
        ms = g_match_mgr.GetMatchList()
        rep = C2LMatchInfo()
        rep.matchs.extend(ms)
        self.Randomcast(rep)


    def OnStartMatch(self, ins):
        if not self.isPresenter(ins.user):
            return
        if ins.is_warmup:
            self.match = g_match_mgr.GetWarmupMatch()
        else:
            self.match = g_match_mgr.GetMatch(ins.match_id)
        if not self.match:
            print "[WARNING]", "start non-exist mid", ins.match_id
            return
        self.achecker = AwardChecker(self.match.race_award, self.match.personal_award)
        def doneLoad():
            self.state.OnNextStep()
        self.qpackage.Load(qid, doneLoad)


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


    def isPresenter(self, user):
        return user.uid == self.presenter.uid


#
class IdleState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.setState(self.room.ready_state)


#
class ReadyState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.setState(self.room.timing_state)


#
class TimingState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.setState(self.room.timing_state)


#
class TimeupState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.setState(self.room.statistics_state)


#
class StatisticsState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.setState(self.room.answer_state)


#
class AnswerState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.setState(self.room.announce_state)




#
class AnnounceState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.setState(self.room.award_state)


#
class AwardState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.setState(self.room.ending_state)


#
class EndingState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.setState(self.room.idle_state)


