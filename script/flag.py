# -*- coding: utf-8 -*-

import time, cPickle, logging, json
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

        self.reset()


    def reset(self):
        self.top1 = None        # top1's capture action ins
        self.uid2action = {}
        self.owner = User()
        self.hp = FLAG_MAX_HP
        self.maxhp = FLAG_MAX_HP
        self.pre_hp = 0


    def changeDoneAction(self, a):
        logging.info("FLAG done action %s --> %s" % (self.done_action, a))
        self.done_action = a
        self.cc.ClearFlag()
        self.pickle()


    def getCountTime(self):
        elapse = int(time.time() - self.start_time)
        if elapse >= (CAPTURE_TIME + NEXT_CAPTURE_CD):
            # waitting for enable
            return 0, 0
        elif elapse >= CAPTURE_TIME:
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
        if not self.canBeStart():
            logging.debug("flag started %s" % self.done_action)
            return
        pb.ret = OK
        self.Unicast(pb, ins.user.uid)
        self.changeDoneAction(Null)
        self.start_time = time.time()
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
            self.notifyFlagMessage(PopupUid, s, self.owner.uid)
            self.changeDoneAction(FirstBlood)
            self.notifyStatus()
            s = u"恭喜你成功夺得战旗！"
            self.notifyFlagMessage(Popup, s, None, self.owner.uid)
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
        #logging.debug("self.uid2action %s" % self.uid2action)

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
        return self.done_action == Disable and self.getCountTime()[0] == 0


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
        self.top1 = None
        self.uid2action = {}


    def makeRestitution(self, uid, action):
        ypoint, re = action.GetRestitution()
        if re == 0:
            return
        s = u"本次战旗争夺中，你一共花费了%dYB, 获得了%d白银的返还奖励。" % (ypoint/10, re)
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
        if ins.action == Attack and ins.user.uid != self.owner.uid:
            self.hp -= ins.point
        if self.hp <= 0:
            t = self.top1.user
            s = u"恭喜%s在攻防战中战果累累，打败%s获得战旗，大家祝贺TA！" % (t.name, self.owner.name)
            self.notifyFlagMessage(PopupUid, s, t.uid)
            s = u"恭喜你，本次攻防战中你成功获得了战旗的拥有权。新的战神，就是你！"
            self.notifyFlagMessage(Popup, s, None, t.uid)
            self.hp = FLAG_MAX_HP
            self.owner.MergeFrom(t)
            self.changeDoneAction(OwnerChange)
            self.notifyStatus()
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
            format=u"恭喜%s最终成功守护战旗，%s将获得6天的战旗拥有权，以及一周内71频道的独家冠名权。"
            s = format % (u"你", u"你")
            self.notifyFlagMessage(Popup, s, None, self.owner.uid)
            s = format % (self.owner.name, u"并")
            self.notifyFlagMessage(PopupUid, s, self.owner.uid)
        else:
            s = u"夺旗结束，各路大侠摩拳擦掌准备着下一轮的战斗，敬请期待！"
            self.notifyFlagMessage(PopupUid, s, 1)
        self.hp = FLAG_MAX_HP
        self.notifyStatus()
        self.settle()
        self.timer.SetTimer1(self.getCountTime()[0], self.onNextCaptureCD)


    def onNextCaptureCD(self):
        self.changeDoneAction(Disable)
        self.reset()
        self.notifyStatus()


    # not necessary to pickle Disable status
    def pickle(self):
        self.cc.CacheFlagStatus(cPickle.dumps(self))


    def goon(self):
        t, c = self.getCountTime()
        if c == 0:
            return
        elif c < 0:
            self.timer.SetTimer1(t, self.onNextCaptureCD)
            return

        self.timer.SetTimer1(t, self.onCaptureTimeup)
        self.timer.SetTimer(SYNC_FLAG_INTERVAL, self.syncFlagStatus)

        for ins in self.cc.GetCaptureActions():
            self.uid2action.update(ins)


