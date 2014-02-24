# -*- coding: utf-8 -*-

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
        return room


    def dispatch(self, tsid, ssid, uri, data):
        cls = URI2CLASS[uri]
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
        print "py dispatch:", tsid, ssid, method_name
        print ins
        try:
            method = getattr(room.state, method_name)
        except:
            try:
                method = getattr(room, method_name)
            except:
                print "not exist method", method_name
            else:
                method(ins)


    def checkInRoom(self, ins):
        try:
            uid = ins.user.uid
            if uid == 0:
                return ins.subsid
        except Exception as err:
            print "check in Room err", err
            return None
        else:
            if ins.DESCRIPTOR.name == "C2LLogin":
                if self.uid2ssid.get(uid) != ins.subsid:
                    self.uid2ssid[uid] = ins.subsid
                    return ins.subsid
            return self.uid2ssid.get(uid)



watchdog = WatchDog()

