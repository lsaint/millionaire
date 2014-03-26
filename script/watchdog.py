# -*- coding: utf-8 -*-

import base64, logging
from uri import *
from room import Room

class WatchDog(object):

    def __init__(self):
        self.ssid2room = {}
        self.uid2ssid = {}


    def gainRoom(self, tsid, ssid):
        room = self.ssid2room.get(ssid)
        if not room:
            room = Room(tsid, ssid)
            self.ssid2room[ssid] = room
        return room


    def dispatch(self, tsid, ssid, uri, data):
        cls = URI2CLASS.get(uri)
        if cls is None:
            logging.warning("not exist uri %d" % uri)
            return
        ins = cls()
        ins.ParseFromString(base64.b64decode(data))
        ssid, uid = self.checkInRoom(ins)
        if not ssid:
            logging.debug("not logined %s" % str(ins).replace("\n", ""))
            return
        room = self.gainRoom(tsid, ssid)
        if uid:
            room.SetPing(uid)
        method_name= "%s%s" % ("On", ins.DESCRIPTOR.name[3:])
        logging.debug("--> %d %d %s: %s" % (
                        tsid, ssid, method_name,
                        str(ins).replace("\n", " ")))
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
            if ins.DESCRIPTOR.name == "C2LLogin":
                self.uid2ssid[uid] = ins.subsid
                return ins.subsid, uid
            ssid = self.uid2ssid.get(uid)
            # user who change sid but did not login yet
            if ins.DESCRIPTOR.name == "F2LNotifyMic1":
                if ssid and ssid != ins.subsid:
                    logging.warn("register ssid not match. uid:%d" % uid)
                    return None, None
            return ssid, uid


watchdog = WatchDog()

