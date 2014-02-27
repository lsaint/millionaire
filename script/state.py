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


#


class IdleState(State):

    def __init__(self, room):
        self.room = room
        self.status = Idle
        self.timer = Timer()


    def OnEnterState(self):
        self.room.reset()

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


#
class TimingState(State):

    def __init__(self, room):
        self.room = room
        self.status = Timing


    def OnEnterState(self):
        self.room.ResetQuestion()
        pb = L2CNotifyTimingStatus()
        pb.question.MergeFrom(self.room.GenNextQuestion())
        pb.start_time = self.room.cur_q_start_time
        self.room.Broadcast(pb)
        self.room.CountTime(pb.question.count_time)


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


#
class StatisticsState(State):

    def __init__(self, room):
        self.room = room
        self.status = Statistics


    def OnEnterState(self):
        self.room.CheckCurAward()
        pb = L2CNotifyStatisticsStatus()
        pb.stati.extend(self.room.stati.GetDistribution())
        awards = self.room.GetCurAward()
        if awards:
            pb.sections.extend(awards)
        self.room.Randomcast(pb)


    def OnNextStep(self, ins):
        self.room.SetState(self.room.answer_state, ins.status)


#
class AnswerState(State):

    def __init__(self, room):
        self.room = room
        self.status = Answer


    def OnEnterState(self):
        pb = L2CNotifyAnswerStatus()
        pb.right_answer.MergeFrom(self.room.GetCurRightAnswer())
        self.room.Randomcast(pb)
        self.room.Settle(pb.right_answer.answer)


    def OnNextStep(self, ins):
        self.room.SetState(self.room.announce_state, ins.status)


#
class AnnounceState(State):

    def __init__(self, room):
        self.room = room
        self.status = Announce


    def OnEnterState(self):
        self.room.CalSurvivorNum()
        pb = L2CNotifyAnnounceStatus()
        pb.win_user_amount = self.room.cur_survivor_num
        pb.topn.extend(self.room.stati.GetTopN())
        self.room.Randomcast(pb)


    def OnNextStep(self, ins):
        if self.room.cur_survivor_num == 0:
            self.room.SetState(self.room.ending_state, ins.status)
            return

        if self.room.GetCurAward():
            self.room.SetState(self.room.award_state, ins.status)
        else:
            self.room.EnterEndingOrTiming(ins.status)



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
        self.room.SetState(self.room.idle_state, ins.status)
        # set timer to idle


