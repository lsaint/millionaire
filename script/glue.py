# -*- coding: utf-8 -*-

import sys; sys.path.extend(["./proto/", "./script/"])
import server_pb2, logic_pb2
import go
import post

from timer import Timer
from watchdog import watchdog



def OnProto(tsid, ssid, uri, data):
    print "python OnProto:", tsid, ssid, uri, len(data)
    watchdog.dispatch(tsid, ssid, uri, data)


def OnTicker():
    Timer.Update()


def OnPostDone(sn, ret):
    post.OnPostDone(sn, ret)


def test():
    print "testtestbanbang"
    #t = Timer()
    #t.SetTimer(3, foo)


def foo():
    pb = logic_pb2.L2CNotifyReadyStatus()
    pb.desc =  "Broadcast-bin"
    go.SendMsg(1, 2, 33, pb.SerializeToString(), server_pb2.Broadcast, 0)
    pb.desc =  "Randomcast-bin"
    go.SendMsg(1, 2, 77, pb.SerializeToString(), server_pb2.Randomcast, 0)
    pb.desc =  "SpecifySend-bin"
    go.SendMsg(1, 2, 77, pb.SerializeToString(), server_pb2.Randomcast, 1059)
    t = Timer()
    t.SetTimer(3, foo)

