# -*- coding: utf-8 -*-

import base64, logging
from uri import *
from room import  NewRoom
from sender import Sender
from logic_pb2 import L2FSyncGameRoomInfos
from cache import CacheCenter

class WatchDog(Sender):

    def __init__(self):
        Sender.__init__(self, 0, 0)
        self.ssid2room = {}
        self.uid2ssid = {}
        self.loadCache()


    def loadCache(self):
        for k, v in CacheCenter.GetCacheState().iteritems():
            tsid, ssid = eval(k)
            room = NewRoom(tsid, ssid, v)
            self.ssid2room[ssid] = room
            for uid, _ in room.uid2player.iteritems():
                self.uid2ssid[uid] = ssid


    def gainRoom(self, tsid, ssid):
        room = self.ssid2room.get(ssid)
        if not room:
            room = NewRoom(tsid, ssid)
            self.ssid2room[ssid] = room
        return room


    def toIns(self, dt, uri, data):
        cls = dt.get(uri)
        if cls:
            ins = cls()
            ins.ParseFromString(base64.b64decode(data))
            return ins


    def getMethodName(self, ins):
        return "%s%s" % ("On", ins.DESCRIPTOR.name[3:])


    def Dispatch(self, tsid, ssid, uri, data):
        if self.globalDispatch(tsid, ssid, uri, data) is None:
            self.roomDispatch(tsid, ssid, uri, data)


    def globalDispatch(self, tsid, ssid, uri, data):
        ins = self.toIns(URI2CLASS_GLOBAL, uri, data)
        if ins:
            return getattr(self, self.getMethodName(ins))(ins)


    def roomDispatch(self, tsid, ssid, uri, data):
        ins = self.toIns(URI2CLASS, uri, data)
        if not ins:
            logging.warning("not exist uri %d" % uri)
            return

        ssid, uid = self.checkInRoom(ins)
        if not ssid:
            logging.debug("not logined %s" % str(ins).replace("\n", ""))
            return
        room = self.gainRoom(tsid, ssid)
        if uid:
            room.SetPing(uid)
        method_name = self.getMethodName(ins)
        logging.debug("--> %d %d %s: %s" % (tsid, ssid, method_name, str(ins).replace("\n", " ")))
        try:
            method = getattr(room, method_name)
        except:
            try:
                method = getattr(room.state, method_name)
            except:
                logging.warning("not exist method: %s" % method_name)
                return
        method(ins)


    def checkInRoom(self, ins):
        try:
            uid = ins.user.uid
            if uid == 0:
                return ins.subsid, uid
        except Exception as err:
            logging.error("checkInRoom %s" % err)
            return None, None
        else:
            return self.uid2ssid.get(uid), uid

    #---

    def OnNotifyMic1(self, ins):
        ssid = self.uid2ssid.get(ins.user.uid)
        # user who change ssid but did not login yet
        if ssid and ssid != ins.subsid:
            logging.warn("register ssid not match. uid:%d" % ins.user.uid)
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



watchdog = WatchDog()

