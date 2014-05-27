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


    def AttackGt(self, other):
        return (not other) or (self.user.uid != other.user.uid and
                                self.action2hp[Attack] >= other.action2hp[Attack])


    def __str__(self):
        return "CaptureAction: %s %s %s" % (self.user, self.action2hp, self.paytype2point)


    def update(self, ins):
        self.action2hp[ins.action] += ins.point
        self.paytype2point[ins.type] += ins.point


    def Name(self):
        return self.user.name


    def Uid(self):
        return self.user.uid


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
        self.top1 = None        # top1's capture action ins
        self.uid2action = {}


    def changeDoneAction(self, a):
        logging.info("FLAG done action %s --> %s" % (self.done_action, a))
        self.done_action = a
        self.cc.ClearFlag()
        self.pickle()


    def getCountTime(self):
        elapse = int(time.time() - self.start_time)
        if elapse > (CAPTURE_TIME + NEXT_CAPTURE_CD):
            # waitting for enable
            return 0, 0
        elif elapse > CAPTURE_TIME:
            # captured CD 
            return NEXT_CAPTURE_CD - (elapse - CAPTURE_TIME), -1
        else:
            # capturing remain time
            return CAPTURE_TIME - elapse, 1


    def OnStartCaptureFlag(self, ins):
        pb = L2CStartCaptureFlagRep()
        pb.ret = FL
        if not self.checkWhitelist(ins.user.uid):
            logging.warn("%d not in flag whitelist" % ins.user.uid)
            return
        if self.isStarted():
            logging.debug("flag started %s" % self.done_action)
            return
        pb.ret = OK
        self.Unicast(pb, ins.user.uid)
        self.changeDoneAction(Null)
        self.start_time = time.time()
        #s = u"当前战旗无主，最先投入Y币夺旗的用户将获得战旗的拥有权。"
        self.notifyStatus()
        self.timer.SetTimer1(CAPTURE_TIME, self.onCaptureTimeup)
        self.timer.SetTimer(SYNC_FLAG_INTERVAL, self.syncFlagStatus)


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
        if self.done_action not in (FirstBlood, OwnerChange):
            logging.debug("capture aciton on err status: %s" % self.done_action)
            return
        a = self.gainaction(ins.user)
        a.update(ins)
        self.cc.CacheCaptureAction(cPickle.dumps(ins))
        logging.debug("self.uid2action %s" % self.uid2action)

        t, s = self.top1, ""
        if ins.action == Attack and t != self.checkAttackTop1(a):
            self.notifyTopAttack(a.Name())
            if t:
                self.notifyFlagMessage(Normal, s)

        self.capturing(ins)


    def OnLogin(self, ins):
        self.Unicast(self.packStatus(), ins.user.uid)
        if self.top1:
            self.notifyTopAttack(self.top1.Name(), ins.user.uid)

### 

    def notifyFlagMessage(self, type, desc, target_uid=None, uid=None):
        pb = L2CNotifyFlagMesssage()
        pb.type = type
        pb.desc = desc
        pb.user.uid = target_uid or 0
        self.UniOrRandomcast(pb, uid)


    def notifyTopAttack(self, name, uid=None):
        self.notifyFlagMessage(Top, u"本次攻防战伤害最高者: %s" % name, None, uid)


    def checkWhitelist(self, uid):
        return True


    def isStarted(self):
        return self.done_action != Disable


    def gainaction(self, user):
        action = self.uid2action.get(user.uid)
        if not action:
            action = CaptureAction(user)
            self.uid2action[user.uid] = action
        return action


    def checkAttackTop1(self, a):
        if a.AttackGt(self.top1):
            self.top1 = a
        return self.top1


    def notifyStatus(self, s=""):
        self.Broadcast(self.packStatus(s))


    def settle(self):
        for uid, action in self.uid2action.iteritems():
            if uid == self.owner.uid:
                continue
            self.makeRestitution(uid, action)
        self.uid2action = {}
        self.top1 = None


    def makeRestitution(self, uid, action):
        ypoint, re = action.GetRestitution()
        if re == 0:
            return
        s = u"本次战旗争夺中，你一共花费了%dYB, 获得了%d白银的返还奖励。" % (ypoint/10, re)
        self.notifyFlagMessage(Popup, s, None, uid)
        VmAddSilver(uid, re)


    def capturing(self, ins):
        if ins.action == Attack and ins.user.uid != self.owner.uid:
            self.hp -= ins.point
        if self.hp <= 0:
            t = self.top1.user
            s = u"恭喜%s在攻防战中战果累累，打败%s获得战旗，大家祝贺TA！" % (t.name, self.owner.name)
            self.hp = FLAG_MAX_HP
            self.owner.MergeFrom(t)
            self.changeDoneAction(OwnerChange)
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
        pb.time = self.getCountTime()[0]
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
            s2 = u"恭喜你最终成功守护战旗，你将获得7天的战旗拥有权，以及71频道的独家冠名权。"
            self.notifyFlagMessage(Popup, s2, None, self.owner.uid)
            s = u"恭喜%s在战旗攻防战中一夫当关，坚持到最后，大家祝贺TA！" % self.owner.name
        self.notifyStatus(s)
        self.settle()
        #self.timer.ReleaseTimer()
        self.timer.SetTimer1(self.getCountTime()[0], self.onNextCaptureCD)


    def onNextCaptureCD(self):
        self.changeDoneAction(Disable)


    # not necessary to pickle Disable status
    def pickle(self):
        self.cc.CacheFlagStatus(cPickle.dumps(self))


    def goon(self):
        t, c = self.getCountTime()
        if c == 0:
            return
        elif c < 0:
            self.onNextCaptureCD()
            return

        self.timer.SetTimer1(t, self.onCaptureTimeup)
        self.timer.SetTimer(SYNC_FLAG_INTERVAL, self.syncFlagStatus)

        for ins in self.cc.GetCaptureActions():
            self.uid2action.update(ins)


