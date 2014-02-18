# -*- coding: utf-8 -*-

import uri
from room import Room

class WatchDog(object):

    def __init__(self):
        self.ssid2room = {}


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
        room = self.gainRoom(tsid, ssid)
        ins = cls()
        ins.ParseFromString(data)
        method_name= "%s%s" % ("On", ins.DESCRIPTOR.name[3:])
        method = getattr(room.state, method_name)
        if not method:
            method = getattr(room, method_name)
            if not method:
                print "not exist method", method_name
                return
        method(ins)


watchdog = WatchDog()

