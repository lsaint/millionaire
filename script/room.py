# -*- coding: utf-8 -*-

from timer import Timer
from sender import Sender
from player import Player
from award import AwardChecker
from match import g_match_mgr
from stati import StatiMgr
from logic_pb2 import *



class Room(Sender):

    def __init__(self, tsid, ssid):
        sender.__init__(self, tsid, ssid)
        self.timer = Timer()
        self.uid2player = {}

        self.idle_state = IdleState(self)
        self.ready_state = ReadyState(self)
        self.timing_state = TimingState(self)
        self.timeup_state = TimeupState(self)
        self.statistics_state = StatisticsState(self)
        self.answer_state = AnswerState(self)
        self.announce_state = AnnounceState(self)
        self.award_state = AwardState(self)
        self.ending_state = EndingState(self)

        self.reset()


    def SetState(self, state):
        self.state = state


    def reset(self):
        self.SetState(self.idle_state)
        self.timer.ReleaseTimer()
        self.timer = Timer()
        self.presenter = None
        self.match = None
        self.achecker = None
        self.qpackage = QuesionPackage()
        self.cur_qid = 0
        self.cur_q_start_time = 0


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


    def GenNextQuestion(self, qid):
        self.cur_qid += 1
        self.cur_q_start_time = int(time.time())
        return self.qpackage.GetQuestion(qid)


    def GetPlayer(self, uid):
        return self.uid2player.get(uid)


    def OnLogin(self, ins):
        player = Player(ins.user)
        player = self.GetPlayer(ins.user.uid)
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
            player = self.GetPlayer(ins.user.uid)
            self.presenter = player
            self.SetState(self.ready_state)
        else:
            pass


    def isPresenter(self, user):
        return user.uid == self.presenter.uid


#
class IdleState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.SetState(self.room.ready_state)


#
class ReadyState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.SetState(self.room.timing_state)
        pb = L2CNotifyTimingStatus()
        pb.question = self.room.GenNextQuestion()
        pb.start_time = self.room.cur_q_start_time
        self.room.Randomcast(pb)
        self.stati = StatiMgr(self.room.qpackage.GetRightAnswer(self.cur_qid))


#
class TimingState(object):

    def __init__(self, room):
        self.room = room


    def OnAnswerQuestion(self, ins):
        if ins.answer.id != self.room.cur_qid:
            return
        player = self.GetPlayer(ins.answer.user.uid)
        self.stati.OnAnswer(player, ins.answer.answer, int(time.time()) - self.cur_q_start_time)


    def OnNextStep(self, ins):
        self.room.SetState(self.room.timeup_state)
        pb = L2CNotifyTimeupStatus()
        self.room.Randomcast(pb)


#
class TimeupState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.SetState(self.room.statistics_state)
        pb = L2CNotifyStatisticsStatus()
        pb.stati.extend(self.room.stati.GetDistribution())
        self.room.Randomcast(pb)


#
class StatisticsState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.SetState(self.room.answer_state)
        pb = L2CNotifyAnswerStatus()
        pb.right_answer = self.room.qpackage.GetRightAnswer(self.cur_qid)
        self.room.Randomcast(pb)


#
class AnswerState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.SetState(self.room.announce_state)




#
class AnnounceState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.SetState(self.room.award_state)


#
class AwardState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.SetState(self.room.ending_state)


#
class EndingState(object):

    def __init__(self, room):
        self.room = room


    def OnNextStep(self, ins):
        self.room.SetState(self.room.idle_state)


