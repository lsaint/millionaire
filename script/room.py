# -*- coding: utf-8 -*-

import time, logging, json, random, cPickle
from timer import Timer, g_timer
from sender import Sender
from state import *
from player import Player
from award import AwardChecker
from match import g_match_mgr
from question import QuesionPackage
from logic_pb2 import *
from config import *
from give import give
from post import PostAsync
from cache import CacheCenter


def NewRoom(tsid, ssid, pickle_data=None):
    if pickle_data:
        try:
            room = cPickle.loads(pickle_data)
            room.goon()
            logging.info("GO ON room %d %d %s" % (tsid, ssid, room.state.Name()))
        except Exception as err:
            logging.error("GO ON room err: %s. clear cache and new room." % err)
            room = Room(tsid, ssid)
            room.cc.Clear()
    else:
        logging.info("no pickle data found")
        room = Room(tsid, ssid)

    return room


class Room(Sender):

    def __init__(self, tsid, ssid):
        Sender.__init__(self, tsid, ssid)
        self.mid = ""
        self.timer = Timer()
        self.uid2player = {}
        self.presenter = None
        self.cache_billboard = {}
        self.cc = CacheCenter(tsid, ssid)

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
        self.loopGetBillboard()


    def pickle(self):
        self.cc.CacheState(cPickle.dumps(self))
        logging.info("[PICKLE]tsid: %d, ssid: %d, status: %s" % (
                                    self.tsid, self.ssid, self.state.Name()))


    # go on after pickled
    def goon(self):
        for uid, name in self.cc.GetLoginoutedPlayers().iteritems():
            if name == "":      # logout
                del self.uid2player[uid]
            else:
                self.uid2player[uid] = Player(uid, name, self.state.status)

        uid = self.cc.GetPresenter()
        if uid != None:
            if uid != 0:
                player = self.GetPlayer(uid)
                player.role = Presenter
                player.ping = time.time()
                self.presenter = player
            else:
                self.presenter = None

        for uid in self.cc.GetRevivedPlayers():
            self.GetPlayer(uid).role = Reviver

        for uid, answer in self.cc.GetPlayerAnswers().iteritems():
            self.GetPlayer(uid).answers[self.cur_qid] = answer

        self.SetState(self.state)


    def GenMid(self):
        self.mid = hex(int(str(int(time.time() * 1000000) + random.randint(0,100000))[6:]))[2:]


    def SetState(self, state, cli_status=None):
        if cli_status and cli_status != self.state.status:
            return
        self.state.OnLeaveState()
        self.state = state
        logging.info("Enter======================================> %s" % state.Name())
        self.cc.Clear()
        self.pickle()
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
        self.winners = []
        self.final_qid = 0
        self.qpackage = QuesionPackage()
        self.resetPlayers()


    def resetPlayers(self):
        map(lambda (k,v): (k, v.Reset()), self.uid2player.iteritems())


    def OnMatchInfo(self, ins):
        ms = g_match_mgr.GetMatchList()
        rep = L2CMatchInfoRep()
        rep.matchs.extend(ms)
        self.Unicast(rep, ins.user.uid)


    def IsStarted(self):
        return not not self.match


    def OnStartMatch(self, ins):
        if not self.isPresenter(ins.user.uid):
            return
        if self.state.status != Ready:
            logging.warn("match started")
            return
        if ins.is_warmup:
            self.match = g_match_mgr.GetWarmupMatch()
        else:
            self.match = g_match_mgr.GetMatch(ins.match_id)
            self.is_warmup = False
        self.qpackage = g_match_mgr.GetQpackage(self.match.pid)
        if not self.match or not self.qpackage:
            logging.warning("start match %d pid %d error" % (ins.match_id, self.qpackage or 0))
            self.match = None
            return
        self.GenMid()
        logging.info("START_MATCH %s %d %d" % (self.mid, self.ssid, ins.match_id))
        self.notifyMatchInfo()
        self.achecker = AwardChecker(self.mid, self.match.race_award, self.match.personal_award)
        self.SetState(self.timing_state)
        self.SetFinalQid()
        self.notifyPreload()


    def notifyPreload(self, uid = None):
        pb = self.qpackage.GetPreloadQuestions()
        if pb:
            self.UniOrRandomcast(pb, uid)


    def notifyMatchInfo(self, uid=None):
        if not self.match:
            return
        pb = L2CNotifyMatchInfo()
        pb.is_warmup = self.is_warmup
        pb.match.MergeFrom(self.match)
        pb.match.ClearField("pid")
        self.UniOrBroadcast(pb, uid)


    def NotifyTiming(self, uid=None):
        pb = L2CNotifyTimingStatus()
        pb.question.MergeFrom(self.GetCurQuestion())
        pb.start_time = self.cur_q_start_time
        self.UniOrBroadcast(pb, uid)


    def NotifyQuestion(self, uid):
        pb = L2CNotifyGameQuestion()
        pb.gq.MergeFrom(self.GetCurQuestion())
        self.Unicast(pb, uid)


    def NotifyStati(self, uid=None):
        pb = L2CNotifyStatisticsStatus()
        pb.stati.extend(self.stati.GetDistribution())
        self.UniOrBroadcast(pb, uid)
        self.stati.LogDistribution()


    def NotifyAnswer(self, uid=None):
        pb = L2CNotifyAnswerStatus()
        pb.right_answer.MergeFrom(self.GetCurRightAnswer())
        self.UniOrBroadcast(pb, uid)


    def NotifyAnnounce(self, uid=None):
        pb = L2CNotifyAnnounceStatus()
        pb.win_user_amount = self.cur_survivor_num
        pb.topn.extend(self.stati.GetTopN())
        awards = self.GetCurAward()
        if awards:
            pb.sections.extend(awards)
        self.UniOrBroadcast(pb, uid)


    def NotifySituation(self, cal_revive=True, uid=None):
        if cal_revive:
            self.CalReviverNum()
            logging.info("S-PCU %d" % len(self.uid2player))
        pb = L2CNotifySituation()
        pb.id = self.cur_qid
        pb.survivor_num = self.cur_survivor_num
        pb.reviver_num = self.cur_reviver_num
        self.UniOrBroadcast(pb, uid)


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
            player = Player(ins.user.uid, ins.user.name, self.state.status)
            self.uid2player[player.uid] = player

        rep = L2CLoginRep()
        rep.user.role = player.role
        rep.ret = OK
        rep.status = self.state.status
        rep.cur_time = int(time.time())
        rep.coef_k = player.CalCoefK(self.cur_qid, self.qpackage.id2rightanswer, self.state.status)
        self.Unicast(rep, player.uid)

        pb = L2CNotifyPresenterChange()
        if self.presenter:
            pb.presenter.uid = self.presenter.uid
        self.Unicast(pb, player.uid)

        self.notifyMatchInfo(player.uid)
        self.notifyPreload(player.uid)

        self.state.OnLogin(ins)
        map(lambda pb: self.Unicast(pb, player.uid), self.cache_billboard.values())

        self.cc.CacheLoginedPlayer(player.uid, player.name)
        logging.info("S-DAU %d" % player.uid)


    def OnTimeSync(self, ins):
        pb = L2CTimeSyncRep()
        pb.sn = ins.sn
        pb.cur_time = int(time.time())
        self.Unicast(pb, ins.user.uid)


    def OnPing(self, ins):
        if self.presenter and ins.user.uid == self.presenter.uid:
            pb = L2CPingRep()
            pb.sn = ins.sn
            self.Unicast(pb, ins.user.uid)
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
            self.state.OnPresenterDown()
            pb = L2CNotifyPresenterChange()
            self.Broadcast(pb)
        self.cc.CachePresenter(0)


    def SetPresenter(self, player):
        player.role = Presenter
        player.ping = time.time()
        self.presenter = player
        self.state.OnPresenterUp()
        pb = L2CNotifyPresenterChange()
        pb.presenter.uid = player.uid
        pb.presenter.name = unicode(player.name)
        self.Broadcast(pb)
        self.cc.CachePresenter(player.uid)


    def OnNotifyMic1(self, ins):
        uid = ins.user.uid
        if uid == 0:
            return self.onMic1Down()
        if self.presenter:
            return self.onMic1Change(uid)
        else:
            return self.onMic1Up(uid)


    def onMic1Down(self):
        if self.presenter:
            self.NegatePresenter(self.presenter)

    def onMic1Up(self, uid):
        player = self.GetPlayer(uid)
        if player and g_match_mgr.IsValidPresenter(uid):
            self.SetPresenter(player)

    def onMic1Change(self, uid):
        if uid == self.presenter.uid:
            return
        player = self.GetPlayer(uid)
        if player and g_match_mgr.IsValidPresenter(uid):
            self.NegatePresenter(self.presenter, True)
            self.SetPresenter(player)
        else:
            self.NegatePresenter(self.presenter)


    def OnRevive(self, ins):
        player = self.GetPlayer(ins.user.uid)
        if player:
            pb = L2FReviveRep()
            pb.user.uid = player.uid
            pb.user.role = player.role
            pb.coef_k = player.CalCoefK(self.cur_qid, self.qpackage.id2rightanswer, self.state.status)
            self.Unicast(pb, player.uid)
            self.NotifySituation(False, player.uid)
        else:
            logging.debug("revive_logout player:%d" % ins.user.uid)


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
                player.bingos[self.cur_qid] = True


    def GetCurRightAnswer(self):
        gq = GameQuestion()
        gq.id = self.cur_qid
        gq.answer = self.qpackage.GetRightAnswer(self.cur_qid)
        return gq


    def CalReviverNum(self):
        self.cur_reviver_num = len(
                tuple(v for (k,v) in self.uid2player.iteritems() if v.role == Reviver))
        logging.debug("CalReviverNum %d %d" % (len(self.uid2player), self.cur_reviver_num))


    def CheckCurAward(self):
        self.winners = []
        is_check_personal = False
        end_id = self.achecker.GetPersonalAwardEndId()
        if end_id:
            if end_id == self.cur_qid:
                is_check_personal = True

        for uid, player in self.uid2player.iteritems():
            if player.role  == Survivor:
                self.winners.append(uid)
            if is_check_personal:
                self.achecker.CheckPersonalAward(self.cur_qid, player)
        self.achecker.CheckRaceAward(self.cur_qid, len(self.winners))


    def GetCurAward(self):
        if not self.is_warmup:
            return self.achecker.GetAward(self.cur_qid)


    def ResetQuestion(self):
        self.winners = []
        self.cur_qid += 1
        self.cur_q_start_time = int(time.time())
        self.stati = StatiMgr(self.cur_qid, self.qpackage.GetRightAnswer(self.cur_qid))
        for uid, player in self.uid2player.iteritems():
            #player.CheckIncCoefK()  # check before transform
            if player.TransformSurvivor():
                self.cur_survivor_num += 1
        return self.cur_qid


    # giving when enter award state
    def RacePrizeGiving(self):
        bounty = self.achecker.RacePrizeGiving(self.cur_qid, self.winners)
        pb = L2CNotifyAwardStatus()
        for uid in self.winners:
            pb.users.add().uid = uid
        pb.bounty = bounty
        self.Broadcast(pb)


    # giving when leave announce state
    def PersonalPrizeGiving(self):
        if not self.achecker.IsGivingPersonalAward():
            return
        uids, bounty = self.achecker.PersonalPrizeGiving()
        pb = L2CNotifyPersonalAward()
        for uid in uids:
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
        t = self.GetCurQuestion().count_time + TIME_COUNT_DELAY
        self.timer.SetTimer1(t, self.SetState, self.timeup_state)


    def OnNotifyRevive(self, ins):
        player = self.GetPlayer(ins.user.uid)
        if player and self.cur_qid == ins.id:
            player.DoRevive(self.state.status)
            logging.info("%s S-REV %d %d" % (self.mid, self.cur_qid, player.uid))
            self.cc.CacheRevivedPlayer(player.uid)
        else:
            pb = L2FNotifyRevieRep()
            pb.ret = FL
            self.Unicast(pb, ins.user.uid)


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
            self.cc.CacheLogoutedPlayer(player.uid)
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


    def ReplyTimeOutAnswer(self, uid):
        rep = L2CAnswerQuestionRep()
        rep.id = self.cur_qid
        rep.ret = TimeOut
        self.Unicast(rep, uid)


    def GetGameRoomInfos(self):
        gri = GameRoomInfo()
        gri.subsid = self.ssid
        gri.id = self.cur_qid
        gri.status = self.state.status
        if self.match:
            gri.match.MergeFrom(self.match)
        return gri


    def GetBillboard(self):
        def done(op, ret):
            items = json.loads(ret)
            if len(items) == 0:
                return
            pb = L2CNotifyBillboard()
            pb.type = op
            for i in items:
                item = pb.items.add()
                item.uid = i["_id"]
                item.name = i["name"]
                item.total = i["total"]
            self.cache_billboard[op] = pb
            self.Randomcast(pb)
        def done_gift(sn, ret):
            try:
                done(GIFT, ret)
            except Exception as err:
                logging.error("done_gift: %s" % err)
        def done_sponsor(sn, ret):
            try:
                done(SPONSOR, ret)
            except Exception as err:
                logging.error("done_sponsor: %s" % err)
        jn = json.dumps({"op": "gift", "param": BILLBOARD_NUM})
        PostAsync(BILLBOARD_URL, jn, done_gift)
        jn = json.dumps({"op": "sponsor", "param": BILLBOARD_NUM})
        PostAsync(BILLBOARD_URL, jn, done_sponsor)


    def loopGetBillboard(self):
        g_timer.DoSetTimer(BILLBOARD_INTERVAL, self.GetBillboard)

