# -*- coding: utf-8 -*-

import go
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
        go.SendMsg(self.tsid, self.ssid, uri, bin, server_pb2.Broadcast, 0)


    def Randomcast(self, ins):
        uri, bin = self.parse(ins)
        go.SendMsg(self.tsid, self.ssid, uri, bin, server_pb2.Randomcast, 0)


    def SpecifySend(self, ins, uid):
        uri, bin = self.parse(ins)
        go.SendMsg(self.tsid, self.ssid, uri, bin, server_pb2.Specify, uid)

