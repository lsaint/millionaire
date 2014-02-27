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
        ssid = self.checkInRoom(ins)
        if not ssid:
            logging.warning("not exist ssid %s" % ssid)
            return
        room = self.gainRoom(tsid, ssid)
        method_name= "%s%s" % ("On", ins.DESCRIPTOR.name[3:])
        logging.debug("dispatch %s:" % method_name)
        logging.debug(str(ins))
        try:
            method = getattr(room.state, method_name)
        except:
            try:
                method = getattr(room, method_name)
            except:
                logging.warning("not exist method: %s" % method_name)
                return
        method(ins)


    def checkInRoom(self, ins):
        try:
            uid = ins.user.uid
            if uid == 0:
                return ins.subsid
        except Exception as err:
            logging.error("checkInRoom %s" % err)
            return None
        else:
            if ins.DESCRIPTOR.name == "C2LLogin":
                if self.uid2ssid.get(uid) != ins.subsid:
                    self.uid2ssid[uid] = ins.subsid
                    return ins.subsid
            return self.uid2ssid.get(uid)



watchdog = WatchDog()

