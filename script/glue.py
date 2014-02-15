# -*- coding: utf-8 -*-

import sys; sys.path.extend(["./proto/", "./script/"])
import server_pb2
import go

from timer import Timer



def OnProto(tsid, ssid, uri, data):
    print "python onProto", tsid, ssid, uri, len(data)


def OnTicker():
    Timer.Update()


def test():
    print "testtestbanbang"
    t = Timer()
    t.SetTimer(3, foo)


def Broadcast(tsid, ssid, uri, bin):
    go.SendMsg(tsid, ssid, uri, bin, server_pb2.Broadcast)


def Randomcast(tsid, ssid, uri, bin):
    go.SendMsg(tsid, ssid, uri, bin, server_pb2.Randomcast)


def foo():
    print "onTimer"
    Broadcast(2080, 1234, 33, "Broadcast-bin")
    Randomcast(2080, 1234, 77, "Randomcast-bin")
    t = Timer()
    t.SetTimer(3, foo)
