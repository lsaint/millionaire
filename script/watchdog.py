# -*- coding: utf-8 -*-

import base64, log
from uri import *
from room import  NewRoom
from sender import Sender
from logic_pb2 import L2FSyncGameRoomInfos
from cache import CacheCenter
from flag import NewFlagMgr
import treasure

class WatchDog(Sender):

    def __init__(self):
        Sender.__init__(self, 0, 0)
        self.ssid2room = {}
        self.uid2ssid = {}
        self.ssid2flag = {}
        self.loadCache()


    def loadCache(self):
        for k, v in CacheCenter.GetCacheState().iteritems():
            tsid, ssid = eval(k)
            room = NewRoom(tsid, ssid, v)
            self.ssid2room[ssid] = room
            for uid, _ in room.uid2player.iteritems():
                self.uid2ssid[uid] = ssid

        for k, v in CacheCenter.GetCacheFlag().iteritems():
            tsid, ssid = eval(k)
            f = NewFlagMgr(tsid, ssid, v)
            self.ssid2flag[ssid] = f


    def gainRoom(self, tsid, ssid):
        room = self.ssid2room.get(ssid)
        if not room:
            room = NewRoom(tsid, ssid)
            self.ssid2room[ssid] = room
        return room


    def gainFlag(self, tsid, uid):
        ssid = self.uid2ssid[uid]
        f = self.ssid2flag.get(ssid)
        if not f:
            f = NewFlagMgr(tsid, ssid)
            self.ssid2flag[ssid] = f
        return f


    def toIns(self, dt, uri, data):
        cls = dt.get(uri)
        if cls:
            ins = cls()
            ins.ParseFromString(base64.b64decode(data))
            return ins


    def getMethodName(self, ins):
        return "%s%s" % ("On", ins.DESCRIPTOR.name[3:])


    def Dispatch(self, tsid, ssid, uri, data, uid):
        ins = None
        for dt, method in ((URI2CLASS_GLOBAL, self.globalDispatch),
                   (URI2CLASS_ROOM, self.roomDispatch),
                   (URI2CLASS_CAPTURE_FLAG, self.captureFlagDispatch)):
            # ParseFromString only once
            if not ins:
                ins = self.toIns(dt, uri, data)
            # go to next dispatch method when upstream return None
            if ins and method(tsid, ssid, uri, data, uid, ins) is not None:
                break


    def globalDispatch(self, tsid, ssid, uri, data, uid, ins):
        return getattr(self, self.getMethodName(ins))(ins)


    def roomDispatch(self, tsid, ssid, uri, data, uid, ins):
        ssid = self.getssid(uid, ins)
        if not ssid:
            log.debug("not logined %s" % str(ins).replace("\n", ""))
            return False
        room = self.gainRoom(tsid, ssid)
        if uid:
            room.SetPing(uid)
        method_name = self.getMethodName(ins)
        log.debug("R--> %d %d %s: %s" % (tsid, ssid, method_name, str(ins).replace("\n", " ")))
        if hasattr(room, method_name):
            method = getattr(room, method_name)
        elif hasattr(room.state, method_name):
            method = getattr(room.state, method_name)
        else:
            return
        return method(ins)


    def captureFlagDispatch(self, tsid, ssid, uri, data, uid, ins):
        if self.uid2ssid.get(uid) is None:
            return
        n = self.getMethodName(ins)
        log.debug("F--> %d %d %s: %s" % (tsid, ssid, n, str(ins).replace("\n", " ")))
        f = self.gainFlag(tsid, uid)
        return getattr(f, n)(ins)


    def checkInRoom(self, ins):
        try:
            uid = ins.user.uid
            if uid == 0:
                return ins.subsid, uid
        except Exception as err:
            log.error("checkInRoom %s" % err)
            return None, None
        else:
            return self.uid2ssid.get(uid), uid


    def getssid(self, uid=None, ins=None):
        if ins and hasattr(ins, "subsid"):
            return ins.subsid
        return self.uid2ssid.get(uid)

    #---

    def OnNotifyMic1(self, ins):
        ssid = self.uid2ssid.get(ins.user.uid)
        # user who change ssid but did not login yet
        if ssid and ssid != ins.subsid:
            log.warn("register ssid not match. uid:%d" % ins.user.uid)
            return True
        return None


    def OnLogin(self, ins):
        self.uid2ssid[ins.user.uid] = ins.subsid
        return None


    def OnRegister(self, ins):
        gris = [room.GetGameRoomInfos() for _, room in self.ssid2room.iteritems()]
        pb = L2FSyncGameRoomInfos()
        pb.rooms.extend(gris)
        self.Unicast(pb, 0, ins.fid)
        return True


    def OnTreasureListall(self):
        return treasure.ListAll(self.ssid2room.values())


watchdog = WatchDog()

