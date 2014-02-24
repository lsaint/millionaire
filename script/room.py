# -*- coding: utf-8 -*-

from timer import Timer
from sender import Sender
from state import *
from player import Player
from award import AwardChecker
from match import g_match_mgr
from question import QuesionPackage
from stati import StatiMgr
from logic_pb2 import *



class Room(Sender):

    def __init__(self, tsid, ssid):
        Sender.__init__(self, tsid, ssid)
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


    def SetState(self, state, cli_status=None):
        if cli_status and cli_status != self.state.status:
            return
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
        self.cur_survivor_num = 0
        self.final_qid = 0


    def OnMatchInfo(self, ins):
        print "OnMatchInfo"
        ms = g_match_mgr.GetMatchList()
        rep = L2CMatchInfoRep()
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
            pb = L2CNotifyMatchInfo()
            pb.is_warmup = ins.is_warmup
            pb.match = self.match
            self.Randomcast(pb)
        self.qpackage.Load(qid, doneLoad)


    def SetFinalQid(self):
        self.final_qid = self.qpackage.GetQuestionCount()
        f = self.achecker.GetFinalId()
        if f and f < self.final_qid:
            self.final_qid = f


    def IsOver(self):
        return self.cur_qid >= self.final_qid or self.cur_survivor_num == 0


    def GenNextQuestion(self, qid):
        self.cur_qid += 1
        self.cur_q_start_time = int(time.time())
        return self.qpackage.GetQuestion(qid)


    def GetPlayer(self, uid):
        return self.uid2player.get(uid)


    def OnLogin(self, ins):
        player = self.GetPlayer(ins.user.uid)
        if not player:
            player = Player(ins.user)
        rep = L2CLoginRep()
        rep.user.role = player.role
        rep.ret = OK
        rep.status = self.state.status
        self.SpecifySend(rep, player.uid)


    def OnTimeSync(self, ins):
        pb = L2CTimeSyncRep()
        pb.sn = ins.sn
        pb.cur_time = int(time.time())
        self.SpecifySend(pb, ins.user.uid)


    def OnPing(self, ins):
        if self.presenter and ins.user.uid == self.presenter.uid:
            pb = L2CPingRep()
            pb.sn = ins.sn
            self.SpecifySend(pb, ins.user.uid)
            self.presenter.ping = time.time()


    def NegatePresenter(self, player):
        player.role = Loser
        player.ping = 0
        self.presenter = None
        pb = L2CNotifyPresenterChange()
        self.Randomcast(pb)


    def SetPresenter(self, player):
        player.role = Presenter
        player.ping = time.time()
        self.presenter = player
        pb = L2CNotifyPresenterChange()
        pb.user.uid = player.uid
        pb.user.name = player.name
        self.Randomcast(pb)


    def OnNotifyMic1(self, ins):
        if self.presenter and self.presenter.uid == ins.user.uid:
            return
        # down
        uid = ins.user.uid
        if uid == 0 and self.presenter:
            self.NegatePresenter(self.presenter)
            return
        # up
        if uid != 0: 
            if (self.presenter and self.presenter.uid != uid) or (not self.presenter):
                player = self.GetPlayer(uid)
                if self.presenter:
                    self.presenter.NegatePresenter(self.presenter)
                self.SetPresenter(player)
                self.SetState(self.ready_state)


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


    def CalSurvivorNum(self):
        for uid, player in self.uid2player.iteritems():
            if player.role == Survivor:
                self.cur_survivor_num += 1


    def CheckCurAward(self):
        return self.achecker.Check(self.cur_qid, self.cur_survivor_num)


    def GetCurAward(self):
        return self.achecker.GetAward(self.cur_qid)


    def TransformReviver2Surivor(self):
        for uid, player in self.uid2player.iteritems():
            player.TurnSurvivor()


    def PrizeGiving(self):
        winners = []
        for uid, player in self.uid2player.iteritems():
            if player.role  == Survivor:
                winners.append(uid)
        bounty = self.achecker.PrizeGiving(self.cur_qid, winners)
        pb = L2CNotifyAwardStatus()
        for uid in winners:
            pb.users.add().uid = uid
        pb.bounty = bounty
        self.Broadcast(pb)



    def EnterEndingOrTiming(self, cli_status):
        if self.IsOver():
            self.SetState(self.ending_state, cli_status)
        else:
            self.SetState(self.timing_state, cli_status)


    def OnNotifyRevive(self, ins):
        player = self.GetPlayer(ins.user.uid)
        if player and self.cur_qid == ins.id:
            player.DoRevive()
        else:
            pb = L2FNotifyRevieRep()
            pb.ret = FL
            self.SpecifySend(pb, ins.user.uid)


