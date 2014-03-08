# -*- coding: utf-8 -*-

import time, logging
from timer import Timer
from sender import Sender
from state import *
from player import Player
from award import AwardChecker
from match import g_match_mgr
from question import QuesionPackage
from logic_pb2 import *
from config import *



class Room(Sender):

    def __init__(self, tsid, ssid):
        Sender.__init__(self, tsid, ssid)
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

        self.SetState(self.idle_state)


    def SetState(self, state, cli_status=None):
        if cli_status and cli_status != self.state.status:
            return
        self.state.OnLeaveState()
        self.state = state
        logging.info("Enter======================================> %s" % state.__class__.__name__)
        self.state.OnEnterState()


    def Reset(self):
        self.timer.ReleaseTimer()
        self.timer = Timer()
        self.match = None
        self.is_warmup = True
        self.achecker = None
        self.stati = None
        self.cur_qid = 0
        self.cur_q_start_time = 0
        self.cur_survivor_num = 0
        self.cur_reviver_num = 0
        self.final_qid = 0
        self.qpackage = QuesionPackage()
        self.resetPlayers()

    
    def resetPlayers(self):
        for uid, player in self.uid2player.iteritems():
            player.Reset()


    def OnMatchInfo(self, ins):
        ms = g_match_mgr.GetMatchList()
        rep = L2CMatchInfoRep()
        rep.matchs.extend(ms)
        self.SpecifySend(rep, ins.user.uid)


    def OnStartMatch(self, ins):
        if not self.isPresenter(ins.user.uid):
            return
        if self.match:
            logging.warn("match started")
            return
        if ins.is_warmup:
            self.match = g_match_mgr.GetWarmupMatch()
        else:
            self.match = g_match_mgr.GetMatch(ins.match_id)
            self.is_warmup = False
        if not self.match:
            logging.warning("start non-exist mid %d"%ins.match_id)
            return
        self.notifyMatchInfo()
        self.achecker = AwardChecker(self.match.race_award, self.match.personal_award)
        def doneLoad():
            self.SetState(self.timing_state)
            self.SetFinalQid()
        self.qpackage.Load(self.match.pid, doneLoad)



    def notifyMatchInfo(self, uid=None):
        if not self.match:
            return
        pb = L2CNotifyMatchInfo()
        pb.is_warmup = self.is_warmup
        pb.match.MergeFrom(self.match)
        pb.match.ClearField("pid")
        self.SendOrBroadcast(pb, uid)


    def NotifyTiming(self, uid=None):
        pb = L2CNotifyTimingStatus()
        pb.question.MergeFrom(self.GetCurQuestion())
        pb.start_time = self.cur_q_start_time
        self.SendOrBroadcast(pb, uid)


    def NotifyQuestion(self, uid):
        pb = L2CNotifyGameQuestion()
        pb.gq.MergeFrom(self.GetCurQuestion())
        self.SpecifySend(pb, uid)


    def NotifyStati(self, uid=None):
        pb = L2CNotifyStatisticsStatus()
        pb.stati.extend(self.stati.GetDistribution())
        self.SendOrRandomcast(pb, uid)


    def NotifyAnswer(self, uid=None):
        pb = L2CNotifyAnswerStatus()
        pb.right_answer.MergeFrom(self.GetCurRightAnswer())
        self.SendOrRandomcast(pb, uid)


    def NotifyAnnounce(self, uid=None):
        pb = L2CNotifyAnnounceStatus()
        pb.win_user_amount = self.cur_survivor_num
        pb.topn.extend(self.stati.GetTopN())
        awards = self.GetCurAward()
        if awards:
            pb.sections.extend(awards)
        self.SendOrRandomcast(pb, uid)


    def NotifySituation(self, cal_revive=True, uid=None):
        if cal_revive:
            self.CalReviverNum()
        pb = L2CNotifySituation()
        pb.id = self.cur_qid
        pb.survivor_num = self.cur_survivor_num
        pb.reviver_num = self.cur_reviver_num
        self.SendOrBroadcast(pb, uid)


    def SetFinalQid(self):
        self.final_qid = self.qpackage.GetQuestionCount()
        f = self.achecker.GetFinalId()
        if f and f < self.final_qid:
            self.final_qid = f


    def IsOver(self):
        return self.cur_qid >= self.final_qid or (
                self.cur_survivor_num == 0 and self.cur_reviver_num == 0)


    def GetCurQuestion(self):
        return self.qpackage.GetQuestion(self.cur_qid)


    def GetPlayer(self, uid):
        return self.uid2player.get(uid)


    def OnLogin(self, ins):
        player = self.GetPlayer(ins.user.uid)
        if not player:
            player = Player(ins.user)
            self.uid2player[player.uid] = player
        player.CalCoefK(self.cur_qid, self.qpackage.id2rightanswer)
        rep = L2CLoginRep()
        rep.user.role = player.role
        rep.ret = OK
        rep.status = self.state.status
        rep.cur_time = int(time.time())
        self.SpecifySend(rep, player.uid)

        pb = L2CNotifyPresenterChange()
        if self.presenter:
            pb.presenter.uid = self.presenter.uid
        self.SpecifySend(pb, player.uid)

        self.notifyMatchInfo(player.uid)

        self.state.OnLogin(ins)


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
        else:
            self.SetPing(ins.user.uid)


    def SetPing(self, uid):
        player = self.GetPlayer(uid)
        if player:
            player.ping = time.time()
            logging.debug("SetPing %d %d" % (player.uid, player.ping))


    def NegatePresenter(self, player, silence=False):
        player.role = Loser
        player.ping = time.time()
        self.presenter = None
        if not silence:
            pb = L2CNotifyPresenterChange()
            self.Randomcast(pb)


    def SetPresenter(self, player):
        player.role = Presenter
        player.ping = time.time()
        self.presenter = player
        pb = L2CNotifyPresenterChange()
        pb.presenter.uid = player.uid
        pb.presenter.name = player.name
        self.Randomcast(pb)


    def OnNotifyMic1(self, ins):
        uid = ins.user.uid
        # down
        if uid == 0 and self.presenter:
            self.NegatePresenter(self.presenter)
            self.state.OnPresenterDown()
            return

        # up
        #if not g_match_mgr.IsValidPresenter(uid):
        #    return
        if uid != 0:
            if (self.presenter and self.presenter.uid != uid) or (not self.presenter):
                player = self.GetPlayer(uid)
                if self.presenter:
                    self.NegatePresenter(self.presenter, True)
                self.SetPresenter(player)
                self.state.OnPresenterUp()


    def OnRevive(self, ins):
        player = self.GetPlayer(ins.user.uid)
        if player:
            pb = L2FReviveRep()
            pb.user.uid = player.uid
            pb.coef_k = player.coef_k
            self.SpecifySend(pb, player.uid)
            self.NotifySituation(False, player.uid)


    def isPresenter(self, uid):
        return self.presenter and uid == self.presenter.uid


    def Settle(self):
        self.cur_survivor_num = 0
        right_answer = self.qpackage.GetRightAnswer(self.cur_qid)
        for uid, player in self.uid2player.iteritems():
            if right_answer != player.GetAnswer(self.cur_qid) and player.role == Survivor:
                player.role = Loser
            if player.role == Survivor:
                self.cur_survivor_num += 1


    def GetCurRightAnswer(self):
        gq = GameQuestion()
        gq.id = self.cur_qid
        gq.answer = self.qpackage.GetRightAnswer(self.cur_qid)
        return gq


    def CalReviverNum(self):
        self.cur_reviver_num = 0
        for uid, player in self.uid2player.iteritems():
            if player.role == Reviver:
                self.cur_reviver_num += 1
        logging.debug("CalReviverNum %d %d" % (len(self.uid2player), self.cur_reviver_num))


    def CheckCurAward(self):
        self.achecker.Check(self.cur_qid, self.cur_survivor_num)


    def GetCurAward(self):
        if not self.is_warmup:
            return self.achecker.GetAward(self.cur_qid)


    def ResetQuestion(self):
        self.cur_qid += 1
        self.cur_q_start_time = int(time.time())
        self.stati = StatiMgr(self.cur_qid, self.qpackage.GetRightAnswer(self.cur_qid))
        for uid, player in self.uid2player.iteritems():
            player.CheckIncCoefK()  # check before transform
            player.TransformSurvivor()
        return self.cur_qid


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


    def StatiAnswer(self, player, answer):
        self.stati.OnAnswer(player, answer, int(time.time()) - self.cur_q_start_time)


    def EnterEndingOrTiming(self, cli_status):
        if self.IsOver():
            self.SetState(self.ending_state, cli_status)
        else:
            self.SetState(self.timing_state, cli_status)


    def CountTime(self):
        t = self.GetCurQuestion().count_time
        self.timer.SetTimer1(t, self.SetState, self.timeup_state)


    def OnNotifyRevive(self, ins):
        player = self.GetPlayer(ins.user.uid)
        if player and self.cur_qid == ins.id:
            player.DoRevive()
        else:
            pb = L2FNotifyRevieRep()
            pb.ret = FL
            self.SpecifySend(pb, ins.user.uid)


    def SettleNoAnswerPlayers(self):
        for uid, player in self.uid2player.iteritems():
            if player.GetAnswer(self.cur_qid) is None and player.role == Survivor:
                player.role = Loser


    def InitCurSurivorNum(self):
        if self.presenter:
            self.cur_survivor_num = len(self.uid2player) - 1
        else:
            self.cur_survivor_num = len(self.uid2player)


    def OnLogout(self, ins):
        player = self.GetPlayer(ins.user.uid)
        if player:
            del self.uid2player[player.uid]
            logging.debug("Logout %d" % player.uid)
        # OnNotifyMic1 will handle presenter logout


    def CheckPing(self):
        now = time.time()
        lost = []
        for uid, player in self.uid2player.iteritems():
            if now - player.ping > PING_LOST:
                lost.append(uid)
                logging.debug("CheckPing Lost %d %d %d" % (uid, now, player.ping))
        for uid in lost:
            del self.uid2player[uid]

