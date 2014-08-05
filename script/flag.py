# -*- coding: utf-8 -*-

import time, cPickle, logging, json, treasure
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
        if ins.action != Attack and ins.action != Heal:
            return
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
        self.timer = Timer()
        self.cc = CacheCenter(tsid, ssid)

        self.reset(True)


    def reset(self, isSetOwner):
        if isSetOwner:
            self.owner = User(name = OFFICIAL_NAME, uid = OFFICIAL_UID)
        self.start_time = 0
        self.done_action = Defended
        self.top1 = None        # top1's capture action ins
        self.uid2action = {}
        self.hp = FLAG_MAX_HP
        self.maxhp = FLAG_MAX_HP
        self.pre_hp = 0
        self.pre_maxhp = 0
        self.limit_timer = 0
        self.own_time = 0


    def changeDoneAction(self, a):
        logging.info("FLAG done action %s --> %s" % (self.done_action, a))
        self.done_action = a


    def cache(self):
        self.cc.ClearFlag()
        self.pickle()


    def getCountTime(self):
        elapse = 0
        if self.done_action == OwnerChange:
            elapse = int(CAPTURE_TIME - (time.time() - self.start_time))
            if elapse < 0:
                elapse = 0
        return elapse


    def OnStartCaptureFlag(self, ins):
        pb = L2CStartCaptureFlagRep()
        pb.ret = FL
        if not self.checkWhitelist(ins.user.uid):
            logging.warn("%d not in flag whitelist" % ins.user.uid)
            return
        if not self.canBeStart():
            logging.debug("flag started %s" % self.done_action)
            return
        pb.ret = OK
        self.Unicast(pb, ins.user.uid)
        self.changeDoneAction(OwnerChange)
        self.owner = User(name = OFFICIAL_NAME, uid = OFFICIAL_UID)
        self.start_time = time.time()
        self.own_time = self.start_time
        self.setCaptureLimitTimer()
        tip = u"夺旗比赛开始，战旗被攻破后对战旗伤害最高的用户将获得战旗。战旗拥有者享受7天战旗拥有权以及一周内71频道冠名权的荣耀！"
        self.notifyStatus(tip)
        self.capture_timer = self.timer.SetTimer1(CAPTURE_TIME, self.onCaptureTimeup)
        self.timer.SetTimer(SYNC_FLAG_INTERVAL, self.syncFlagStatus)
        treasure.UpdateStatus(self.ssid, 1)
        self.cache()


    # owner Defended if on one defeat her/him in x min
    def setCaptureLimitTimer(self):
        if self.limit_timer:
            self.timer.KillTimer(self.limit_timer)
        self.limit_timer = self.timer.SetTimer1(OWNER_WIN_TIME, self.onCaptureTimeup)
        self.own_time = int(time.time())


    def OnCaptureAction(self, ins):
        if ins.user.uid == self.owner.uid and ins.action == Attack:
            logging.debug("attacking itself %d" % self.owner.uid)
            return

        if self.done_action not in (FirstBlood, OwnerChange):
            logging.debug("capture aciton on err status: %s" % self.done_action)
            return
        a = self.gainaction(ins.user)
        a.update(ins)
        self.cc.CacheCaptureAction(cPickle.dumps(ins))
        #logging.debug("self.uid2action %s" % self.uid2action)

        if ins.action == Inc_Max and self.maxhp < MAX_HP_LIMITATION:
            self.maxhp += ins.point
            if self.maxhp > MAX_HP_LIMITATION:
                self.maxhp = MAX_HP_LIMITATION
            logging.debug("capture aciton add %d point to maxhp, final %d" % (ins.point, self.maxhp) )
        
        t = self.top1
        if ins.action == Attack and t != self.checkAttackTop1(a):
            self.notifyTopAttack(a.Name(), a.Uid())
            if t:
                s = u"当前夺旗攻防战中，%s超越%s，对战旗伤害最高。" % (a.Name(), t.Name())
                self.notifyFlagMessage(Normal, s)

        self.capturing(ins)


    def OnLogin(self, ins):
        self.Unicast(self.packStatus(), ins.user.uid)
        if self.top1:
            self.notifyTopAttack(self.top1.Name(), self.top1.Uid(), ins.user.uid)

### 

    def notifyFlagMessage(self, type, desc, ta_uid=None, uid=None):
        pb = L2CNotifyFlagMesssage()
        pb.type = type
        pb.desc = desc
        pb.user.uid = ta_uid or 0
        self.UniOrRandomcast(pb, uid)


    def notifyTopAttack(self, name, ta_uid=None, uid=None):
        self.notifyFlagMessage(Top, u"本次攻防战伤害最高者: %s" % name, ta_uid, uid)


    def checkWhitelist(self, uid):
        return True


    def canBeStart(self):
        return self.getCountTime() == 0


    def gainaction(self, user):
        action = self.uid2action.get(user.uid)
        if not action:
            action = CaptureAction(user)
            self.uid2action[user.uid] = action
        return action


    def checkAttackTop1(self, a):
        if a.AttackGt(self.top1):
            self.top1 = a
            self.cc.CacheFlagTop1(self.top1.Uid())
        return self.top1


    def notifyStatus(self, s=""):
        self.Broadcast(self.packStatus(s))


    def settle(self):
        for uid, action in self.uid2action.iteritems():
            if uid == self.owner.uid:
                continue
            self.makeRestitution(uid, action)
        self.top1 = None
        self.uid2action = {}


    def makeRestitution(self, uid, action):
        ypoint, re = action.GetRestitution()
        if re == 0:
            return
        s = u"本次战旗争夺中，你一共花费了%.1fYB, 获得了%d白银的返还奖励。" % (ypoint/10.0, re)
        self.notifyFlagMessage(Popup, s, None, uid)

        def done(sn, ret):
            logging.info("VM_ADD_SILVER %d %d, ret: %s" % (uid, re, ret))
            dt = json.loads(ret)
            if dt["op_ret"] == 1:
                pb = L2CNotifyMoneyChange()
                pb.silver = re
                pb.gold = 0
                self.Unicast(pb, uid)
        VmAddSilver(uid, re, done)



    def capturing(self, ins):
        if ins.action == Attack:
            self.hp -= ins.point
        if self.hp <= 0:
            t = self.top1.user
            s = u"恭喜%s在攻防战中战果累累，打败%s获得战旗，大家祝贺TA！" % (t.name, self.owner.name)
            self.notifyFlagMessage(PopupUid, s, t.uid)
            s = u"恭喜你，本次攻防战中你成功获得了战旗的拥有权。新的战神，就是你！"
            self.notifyFlagMessage(Popup, s, None, t.uid)
            self.hp = FLAG_MAX_HP
            self.maxhp = FLAG_MAX_HP
            self.owner.MergeFrom(t)
            self.changeDoneAction(OwnerChange)
            self.setCaptureLimitTimer()
            self.notifyStatus()
            self.settle()
            self.cache()
        if ins.action == Heal:
            self.hp += ins.point
            if self.hp > self.maxhp:
                self.hp = self.maxhp


    def packStatus(self, tip=""):
        pb = L2CNotifyFlagStatus()
        pb.owner.MergeFrom(self.owner)
        pb.hp = self.hp
        pb.maxhp = self.maxhp
        pb.action = self.done_action
        pb.time = self.getCountTime()
        pb.tip = tip
        t = OWNER_WIN_TIME - int(time.time() - self.own_time)
        if t < 0:
            t = 0
        pb.owner_win_time = t
        return pb


    def syncFlagStatus(self):
        if self.pre_hp != self.hp or self.pre_maxhp != self.maxhp:
            self.Randomcast(self.packStatus())
            self.pre_hp = self.hp
            self.pre_maxhp = self.maxhp

    def onCaptureTimeup(self):
        self.timer.KillTimer(self.limit_timer)
        self.timer.KillTimer(self.capture_timer)
        self.changeDoneAction(Defended)
        format=u"恭喜%s最终成功守护战旗，%s将获得6天的战旗拥有权，以及一周内71频道的独家冠名权。"
        s = format % (u"你", u"你")
        self.notifyFlagMessage(Popup, s, None, self.owner.uid)
        s = format % (self.owner.name, u"并")
        self.notifyFlagMessage(PopupUid, s, self.owner.uid)
        self.settle()
        self.abort(False)
        self.cache()


    def abort(self, isSetOwner):
        self.reset(isSetOwner)
        self.notifyStatus()
        treasure.UpdateStatus(self.ssid, 0)


    def OnChangeGameMode(self, ins):
        self.abort(self.done_action==OwnerChange)


    def pickle(self):
        self.cc.CacheFlagStatus(cPickle.dumps(self))


    def goon(self):
        t = self.getCountTime()
        if t == 0:
            return

        limit_time = OWNER_WIN_TIME - int(time.time() - self.own_time)
        if limit_time > 0:
            self.limit_timer = self.timer.SetTimer1(limit_time, self.onCaptureTimeup)
        self.capture_timer = self.timer.SetTimer1(t, self.onCaptureTimeup)
        self.timer.SetTimer(SYNC_FLAG_INTERVAL, self.syncFlagStatus)

        for ins in self.cc.GetCaptureActions():
            a = self.gainaction(ins.user)
            a.update(ins)
            self.capturing(ins)
        self.top1 = self.uid2action.get(self.cc.GetFlagTop1())

