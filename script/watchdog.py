# -*- coding: utf-8 -*-

import uri
from room import Room

class WatchDog(object):

    def __init__(self):
        self.ssid2room = {}
        self.uid2ssid = {}


    def gainRoom(self, tsid, ssid):
        room = self.ssid2room.get(ssid)
        if not room:
            room = Room(tsid, ssid)
        return room


    def dispatch(self, tsid, ssid, uri, data):
        cls = uri.URI2NAME[uri]
        if cls is None:
            print "not exist uri", uri
            return
        ins = cls()
        ins.ParseFromString(data)
        ssid = self.checkInRoom(ins)
        if not ssid:
            print "not exist ssid"
            return
        room = self.gainRoom(tsid, ssid)
        method_name= "%s%s" % ("On", ins.DESCRIPTOR.name[3:])
        method = getattr(room.state, method_name)
        if not method:
            method = getattr(room, method_name)
            if not method:
                print "not exist method", method_name
                return
        method(ins)


    def checkInRoom(self, ins):
        try:
            uid = ins.user.uid
            if uid == 0:
                return ins.subsid
        except Exception as err:
            print "checkInRoom err", err
            return None
        if ins.DESCRIPTOR.name == "C2LLogin":
            if self.uid2ssid.get(uid) != ins.subsid:
                self.uid2ssid[uid] = ins.subsid
                return ins.subsid
        else:
            return self.uid2ssid.get(uid)




watchdog = WatchDog()

