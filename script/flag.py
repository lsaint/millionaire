# -*- coding: utf-8 -*-

import time, cPickle, logging
from sender import Sender
from logic_pb2 import *
from timer import Timer
from config import *
from cache import CacheCenter
from award import VmAddSilver


def NewFlagMgr(tsid, ssid, pickle_data=None):
    if pickle_data:
        try:
            f = cPickle.loads(pickle_data)
            f.goon()
            logging.info("GO ON flag %d %d" % (tsid, ssid))
        except Exception as err:
            logging.error("GO ON flag err: %s. clear cache and new flag." % err)
            f = FlagMgr(tsid, ssid)
            f.cc.ClearFlag()
    else:
        logging.info("no flag pickle data found")
        f = FlagMgr(tsid, ssid)
    return f



class CaptureAction(object):

    def __init__(self, user):
        self.user = user
        self.action2hp = {Attack: 0, Heal: 0}
        self.paytype2point = {YB: 0, SILVER: 0}


    def __cmp__(self, other):
        return self.action2hp[Attack].__cmp__(other.action2hp[Attack])


    def update(self, ins):
        self.action2hp[ins.action] += ins.point
        self.paytype2point[ins.type] += ins.point


    def Name(self):
        return self.user.name


    def GetRestitution(self):
        ypoint = self.paytype2point[YB]
        if ypoint != 0:
            return ypoint, int(ypoint * COEF_RESTITUTION)
        return 0, 0


class FlagMgr(Sender):

    def __init__(self, tsid, ssid):
        Sender.__init__(self, tsid, ssid)
        self.done_action = Disable
        self.timer = Timer()
        self.cc = CacheCenter(tsid, ssid)
        self.start_time = 0
        self.owner = User()
        self.hp = FLAG_MAX_HP
        self.maxhp = FLAG_MAX_HP
        self.pre_hp = 0
        self.top1 = None
        self.uid2action = {}


    def changeDoneAction(self, a):
        self.done_action = a
        self.cc.ClearFlag()
        self.pickle()


    def OnStartCaptureFlag(self, ins):
        pb = L2CStartCaptureFlagRep()
        pb.ret = FL
        if not self.checkWhitelist(ins.user.uid):
            logging.warn("%d not in flag whitelist" % ins.user.uid)
            return
        if self.isStarted():
            logging.debug("flag started")
            return
        pb.ret = OK
        self.Unicast(pb, ins.user.uid)
        self.changeDoneAction(Null)
        self.start_time = time.time()
        s = u"当前战旗无主，最先投入Y币夺旗的用户将获得战旗的拥有权。"
        self.notifyStatus(s)
        self.timer.SetTimer1(CAPTURE_TIME, self.onCaptureTimeup)
        self.timer.SetTimer(SYNC_FLG_INTERVAL, self.syncFlagStatus)


    def OnFirstBlood(self, ins):
        rep = L2FFirstBloodRep()
        rep.user.uid = ins.user.uid
        if self.owner.uid == 0:
            self.owner = ins.user
            rep.ret = OK
            s = u"恭喜%s抢先一步，获得战旗。%s" % (ins.user.name,
                                u"其他用户可对战旗发起攻击或守护，战旗被攻破后贡献最高者将夺得战旗")
            self.changeDoneAction(FirstBlood)
            self.notifyStatus(s)
        else:
            rep.ret = FL
        self.Unicast(rep, rep.user.uid)


    def OnCaptureAction(self, ins):
        a = self.getaction(ins.user)
        a.update(ins)
        self.cc.CacheCaptureAction(cPickle.dumps(ins))

        t, s = self.top1, ""
        pb = L2CNotifyFlagMesssage()
        if t != self.checkAttackTop1(a):
            if not t:
                s = u"本次攻防战伤害最高者: %s" % a.Name()
                pb.type = Top
            else:
                s = u"当前夺旗攻防战中，%s超越%s，对战旗伤害最高。" % (a.Name(), t.Name())
                pb.type = Normal
        pb.desc = s
        self.Randomcast(pb)

        self.capturing(ins)


    def OnLogin(self, ins):
        self.Unicast(self.packStatus(), ins.user.uid)

### 

    def checkWhitelist(self, uid):
        return True


    def isStarted(self):
        return self.done_action != Disable


    def getaction(self, user):
        return self.uid2action.get(user.uid) or CaptureAction(user)


    def checkAttackTop1(self, a):
        if not self.top1 or a > self.top1:
            self.top1 = a
        return self.top1


    def notifyStatus(self, s):
        self.Broadcast(self.packStatus(s))


    def settle(self):
        for uid, action in self.uid2action.iteritems():
            if uid == self.owner.uid:
                continue
            self.makeRestitution(uid, action)
        self.uid2action = {}


    def makeRestitution(self, uid, action):
        ypoint, re = action.GetRestitution()
        if re == 0:
            return
        pb = L2CNotifyFlagMesssage()
        pb.type = Popup
        pb.desc = u"本次战旗争夺中，你一共花费了%dYB, 获得了%d白银的返还奖励。" % (ypoint/10, re)
        self.Unicast(pb, uid)
        VmAddSilver(uid, re)


    def capturing(self, ins):
        if ins.action == Attack:
            self.hp -= ins.point
        if self.hp <= 0:
            t = self.owner
            self.owner = ins.user
            self.hp = FLAG_MAX_HP
            self.changeDoneAction(OwnerChange)
            s = u"恭喜%s在攻防战中战果累累，打败%s获得战旗，大家祝贺TA！" % (t.name, self.owner.name)
            self.notifyStatus(s)
            self.settle()
        if ins.action == Heal:
            self.hp += ins.point
            if self.hp > FLAG_MAX_HP:
                self.hp = FLAG_MAX_HP


    def packStatus(self, tip=""):
        pb = L2CNotifyFlagStatus()
        pb.owner.MergeFrom(self.owner)
        pb.hp, pb.maxhp = self.hp, FLAG_MAX_HP
        pb.action = self.done_action
        pb.time = int(time.time() - self.start_time)
        pb.tip = tip
        return pb


    def syncFlagStatus(self):
        if self.pre_hp != self.hp:
            self.Randomcast(self.packStatus())
            self.pre_hp = self.hp


    def onCaptureTimeup(self):
        self.changeDoneAction(Defended)
        s = ""
        if self.owner.uid != 0:
            s = u"恭喜%s在战旗攻防战中一夫当关，坚持到最后，大家祝贺TA！" % self.owner.name
            pb = L2CNotifyFlagMesssage()
            pb.type = Popup
            pb.desc = u"恭喜你最终成功守护战旗，你将获得7天的战旗拥有权，以及71频道的独家冠名权。"
            self.Unicast(pb, self.owner.uid)
        self.notifyStatus(s)
        self.settle()
        self.timer.ReleaseTimer()


    # not necessary to pickle Disable status
    def pickle(self):
        self.cc.CacheFlagStatus(cPickle.dumps(self))


    def goon(self):
        elapse = int(time.time() - self.start_time)
        if  elapse >= CAPTURE_TIME:
            self.onCaptureTimeup()
            return
        else:
            self.timer.SetTimer1(CAPTURE_TIME - elapse, self.onCaptureTimeup)
        self.timer.SetTimer(SYNC_FLG_INTERVAL, self.syncFlagStatus)

        for ins in self.cc.GetCaptureActions():
            self.uid2action.update(ins)


