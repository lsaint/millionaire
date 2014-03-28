# -*- coding: utf-8 -*-

import go, logging
from uri import CLASS2URI
import server_pb2
import base64

class Sender(object):


    def __init__(self, tsid, ssid):
        self.tsid = tsid 
        self.ssid = ssid


    def parse(self, ins):
        cls = ins.__class__
        uri = CLASS2URI.get(cls)
        bin = ins.SerializeToString()
        return uri, base64.b64encode(bin)


    def Broadcast(self, ins):
        uri, bin = self.parse(ins)
        go.SendMsg(self.tsid, self.ssid, uri, bin, server_pb2.Broadcast, 0, 0)
        logging.debug("<--Broadcast %d %d %s: %s" % (
                        self.tsid, self.ssid,
                        ins.DESCRIPTOR.name, str(ins).replace("\n", " ")))


    def Randomcast(self, ins):
        uri, bin = self.parse(ins)
        go.SendMsg(self.tsid, self.ssid, uri, bin, server_pb2.Randomcast, 0, 0)
        logging.debug("<--Randomcast %d %d %s: %s" % (
                        self.tsid, self.ssid,
                        ins.DESCRIPTOR.name, str(ins).replace("\n", " ")))


    def Unicast(self, ins, uid, fid=0):
        uri, bin = self.parse(ins)
        go.SendMsg(self.tsid, self.ssid, uri, bin, server_pb2.Unicast, uid, fid)
        logging.debug("<--Unicast %d %d %d %s: %s" % (
                        self.tsid, self.ssid,
                        uid, ins.DESCRIPTOR.name, str(ins).replace("\n", " ")))


    def UniOrRandomcast(self, ins, uid):
        if uid:
            self.Unicast(ins, uid)
        else:
            self.Randomcast(ins)


    def UniOrBroadcast(self, ins, uid):
        if uid:
            self.Unicast(ins, uid)
        else:
            self.Broadcast(ins)

