# -*- coding: utf-8 -*-

import sys; sys.path.extend(["./proto/", "./script/"])
import logic_pb2

from timer import Timer



def OnProto(tsid, ssid, uri, data):
    print "python onProto", tsid, ssid, uri, len(data)


def OnTicker():
    Timer.Update()


def test():
    print "testtestbanbang"
    import go
    go.SendMsg(1, 2, 3, "lSaint", 1)
    t = Timer()
    t.SetTimer(3, foo)


def Broadcast(tsid, ssid, uri, bin):
    go.SendMsg(tsid, ssid, uri, bin, logic_pb2.Braoadcast)


def Randomcast(tsid, ssid, uri, bin):
    go.SendMsg(tsid, ssid, uri, bin, logic_pb2.Randomcast)


def foo():
    print "onTimer"
