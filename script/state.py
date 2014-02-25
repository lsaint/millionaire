# -*- coding: utf-8 -*-

from logic_pb2 import *
from stati import StatiMgr

class IdleState(object):

    def __init__(self, room):
        self.room = room
        self.status = Idle


    def OnEnterState(self):
        pass


    def OnNextStep(self, ins):
        self.room.SetState(self.room.ready_state, ins.status)


#
class ReadyState(object):

    def __init__(self, room):
        self.room = room
        self.status = Ready


    def OnEnterState(self):
        pass


    def OnNextStep(self, ins):
        self.room.SetState(self.room.timing_state, ins.status)


#
class TimingState(object):

    def __init__(self, room):
        self.room = room
        self.status = Timing


    def OnEnterState(self):
        self.room.TransformReviver2Surivor()
        pb = L2CNotifyTimingStatus()
        pb.question.MergeFrom(self.room.GenNextQuestion())
        pb.start_time = self.room.cur_q_start_time
        self.room.Broadcast(pb)
        self.stati = StatiMgr(self.room.GetCurRightAnswer())


    def OnAnswerQuestion(self, ins):
        if ins.answer.id != self.room.cur_qid:
            return
        player = self.GetPlayer(ins.answer.user.uid)
        if not player:
            return
        if not player.DoAnswer(ins.answer.id, ins.answer.answer):
            return
        self.stati.OnAnswer(player, ins.answer.answer, int(time.time()) - self.cur_q_start_time)


    def OnNextStep(self, ins):
        self.room.SetState(self.room.timeup_state, ins.status)


#
class TimeupState(object):

    def __init__(self, room):
        self.room = room
        self.status = Timeup


    def OnEnterState(self):
        pb = L2CNotifyTimeupStatus()
        self.room.Randomcast(pb)


    def OnNextStep(self, ins):
        self.room.SetState(self.room.statistics_state, ins.status)


#
class StatisticsState(object):

    def __init__(self, room):
        self.room = room
        self.status = Statistics


    def OnEnterState(self):
        self.room.CheckCurAward()
        pb = L2CNotifyStatisticsStatus()
        pb.stati.extend(self.room.stati.GetDistribution())
        pb.sections = self.room.GetCurAward()
        self.room.Randomcast(pb)


    def OnNextStep(self, ins):
        self.room.SetState(self.room.answer_state, ins.status)


#
class AnswerState(object):

    def __init__(self, room):
        self.room = room
        self.status = Answer


    def OnEnterState(self):
        pb = L2CNotifyAnswerStatus()
        pb.right_answer = self.room.GetRightAnswer()
        self.room.Randomcast(pb)
        self.room.Settle(pb.right_answer)


    def OnNextStep(self, ins):
        self.room.SetState(self.room.announce_state, ins.status)


#
class AnnounceState(object):

    def __init__(self, room):
        self.room = room
        self.status = Announce


    def OnEnterState(self):
        self.room.CalSurvivorNum()
        pb = L2CNotifyAnnounceStatus()
        pb.win_user_amount = self.room.cur_survivor_num
        pb.topn.extend(self.question.GetTopN())
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
class AwardState(object):

    def __init__(self, room):
        self.room = room
        self.status = Award


    def OnEnterState(self):
        self.room.PrizeGiving()


    def OnNextStep(self, ins):
        self.room.EnterEndingOrTiming(ins.status)


#
class EndingState(object):

    def __init__(self, room):
        self.room = room
        self.status = Ending


    def OnEnterState(self):
        pb = L2CNotifyEndingStatus()
        self.room.Randomcast(pb)


    def OnNextStep(self, ins):
        self.room.SetState(self.room.idle_state, ins.status)
        # set timer to idle


