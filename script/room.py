# -*- coding: utf-8 -*-

from timer import Timer
from sender import Sender
from state import *
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
        self.state.OnEnterState()


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
        self.final_qid = 0


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
            self.SetFinalQid()
        self.qpackage.Load(qid, doneLoad)


    def SetFinalQid(self):
        self.final_qid = self.qpackage.GetQuestionCount()
        f = self.achecker.GetFinalId()
        if f and f < self.final_qid:
            self.final_qid = f


    def IsOver(self):
        return self.cur_qid >= self.final_qid


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


    def OnNotifyRevive(self, ins):
        player = self.GetPlayer(ins.user.uid)
        if not player:
            return
        player.DoRevive()


    def isPresenter(self, user):
        return user.uid == self.presenter.uid


    def Settle(self, right_answer):
        for player, uid in self.uid2player.iteritems():
            if right_answer != player.GetAnswer(self.cur_qid) and player.role != Presenter:
                player.role = Loser


    def GetCurRightAnswer(self):
        return self.qpackage.GetRightAnswer(self.cur_qid)


    def GetSurvivorNum(self):
        num = 0
        for uid, player in self.uid2player.iteritems():
            if player.role == Survivor:
                num += 1
        return num


    def CheckCurRaceAward(self):
        return self.achecker.CheckRaceAward(self.cur_qid, self.GetSurvivorNum())


    def SetReviver2Surivor(self):
        for uid, player in self.uid2player.iteritems():
            player.TurnSurvivor()


    def PrizeGiving(self):
        return self.achecker.PrizeGiving(self.cur_qid)


    def EnterEndingOrTiming(self):
        if self.IsOver():
            self.SetState(self.ending_state)
        else:
            self.SetState(self.timing_state)

