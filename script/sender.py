# -*- coding: utf-8 -*-

import go
import uri
import server_pb2

class Sender(object):


    def __init__(self, tsid, ssid):
        self.tsid = tsid 
        self.ssid = ssid


    def parse(self, ins):
        cls = ins.__class__
        uri = uri.CLASS2URI.get(cls)
        bin = ins.SerializeToString()
        return uri, bin


    def Broadcast(self, ins):
        uri, bin = self.parse(ins)
        go.SendMsg(selftsid, self.ssid, uri, bin, server_pb2.Broadcast)


    def Randomcast(self, ins):
        uri, bin = self.parse(ins)
        go.SendMsg(selftsid, self.ssid, uri, bin, server_pb2.Randomcast)

