# -*- coding: utf-8 -*-

import time, logging

from logic_pb2 import *
from timer import Timer
from stati import StatiMgr
from match import g_match_mgr, LOAD_PREVIEW_INTERVAL



class State(object):

    def OnEnterState(self):
        pass

    def OnLeaveState(self):
        pass

    def OnNextStep(self, ins):
        pass

    def OnLogin(self, ins):
        pass

    def OnPresenterUp(self):
        pass

    def OnPresenterDown(self):
        pass

#


class IdleState(State):

    def __init__(self, room):
        self.room = room
        self.status = Idle
        self.timer = Timer()


    def OnEnterState(self):
        self.room.Reset()

        pb = L2CNotifyIdleStatus()
        self.room.Randomcast(pb)
        self.timer.SetTimer(LOAD_PREVIEW_INTERVAL, self.checkShowPreview)


    def checkShowPreview(self):
        pv = g_match_mgr.GetPreview()
        if pv:
            pb = L2CNotifyPreview()
            pb.MergeFrom(pv)
            self.room.Randomcast(pb)


    def OnLeaveState(self):
        self.timer.ReleaseTimer()


    def OnNextStep(self, ins):
        self.room.SetState(self.room.ready_state, ins.status)


    def OnPresenterUp(self):
        self.room.SetState(self.room.ready_state)



#
class ReadyState(State):

    def __init__(self, room):
        self.room = room
        self.status = Ready


    def OnEnterState(self):
        pb = L2CNotifyReadyStatus() 
        pb.desc = "ready"
        self.room.Randomcast(pb)


    def OnNextStep(self, ins):
        self.room.SetState(self.room.timing_state, ins.status)


    def OnPresenterDown(self):
        self.room.SetState(self.room.idle_state)


#
class TimingState(State):

    def __init__(self, room):
        self.room = room
        self.status = Timing


    def OnEnterState(self):
        self.room.ResetQuestion()
        self.room.NotifyTiming()
        self.room.CountTime()


    def OnAnswerQuestion(self, ins):
        if ins.answer.answer.id != self.room.cur_qid:
            return
        player = self.room.GetPlayer(ins.answer.user.uid)
        if not player:
            return
        if not player.DoAnswer(ins.answer.answer.id, ins.answer.answer.answer):
            return
        self.room.StatiAnswer(player, ins.answer.answer.answer)


    def OnNextStep(self, ins):
        logging.warning("invalid next step in timing state")


    def OnLogin(self, ins):
        self.room.NotifyTiming(ins.user.uid)


#
class TimeupState(State):

    def __init__(self, room):
        self.room = room
        self.status = Timeup


    def OnEnterState(self):
        pb = L2CNotifyTimeupStatus()
        self.room.Randomcast(pb)


    def OnNextStep(self, ins):
        self.room.SetState(self.room.statistics_state, ins.status)


    def OnLogin(self, ins):
        self.room.NotifyQuestion(ins.user.uid)


#
class StatisticsState(State):

    def __init__(self, room):
        self.room = room
        self.status = Statistics


    def OnEnterState(self):
        self.room.CheckCurAward()
        self.room.NotifyStati()


    def OnNextStep(self, ins):
        self.room.SetState(self.room.answer_state, ins.status)


    def OnLogin(self, ins):
        self.room.NotifyStati(ins.user.uid)


    def OnLogin(self, ins):
        self.room.NotifyQuestion(ins.user.uid)


#
class AnswerState(State):

    def __init__(self, room):
        self.room = room
        self.status = Answer


    def OnEnterState(self):
        self.room.NotifyAnswer()
        self.room.Settle()


    def OnNextStep(self, ins):
        self.room.SetState(self.room.announce_state, ins.status)


    def OnLogin(self, ins):
        self.room.NotifyQuestion(ins.user.uid)
        self.room.NotifyAnswer(ins.user.uid)


#
class AnnounceState(State):

    def __init__(self, room):
        self.room = room
        self.status = Announce


    def OnEnterState(self):
        self.room.CalSurvivorNum()
        self.room.NotifyAnnounce()


    def OnNextStep(self, ins):
        if self.room.cur_survivor_num == 0:
            self.room.SetState(self.room.ending_state, ins.status)
            return

        if self.room.GetCurAward():
            self.room.SetState(self.room.award_state, ins.status)
        else:
            self.room.EnterEndingOrTiming(ins.status)


    def OnLogin(self, ins):
        self.room.NotifyAnnounce(ins.user.uid)


#
class AwardState(State):

    def __init__(self, room):
        self.room = room
        self.status = Award


    def OnEnterState(self):
        self.room.PrizeGiving()


    def OnNextStep(self, ins):
        self.room.EnterEndingOrTiming(ins.status)


#
class EndingState(State):

    def __init__(self, room):
        self.room = room
        self.status = Ending


    def OnEnterState(self):
        pb = L2CNotifyEndingStatus()
        self.room.Randomcast(pb)


    def OnNextStep(self, ins):
        if ins.status == self.status and self.room.presenter:
            self.room.Reset()
            self.room.SetState(self.room.ready_state)
        # set timer to idle


