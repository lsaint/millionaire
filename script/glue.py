# -*- coding: utf-8 -*-

import sys; sys.path.extend(["./proto/", "./script/"])
import server_pb2, logic_pb2
import go

from timer import Timer
from watchdog import watchdog



def OnProto(tsid, ssid, uri, data):
    print "python onProto", tsid, ssid, uri, len(data)
    watchdog.dispatch(tsid, ssid, uri, data)


def OnTicker():
    Timer.Update()


sn = 1
g_post_callback = {}
def OnPostDone(sn, ret):
    cb = g_post_callback.get(sn)
    if cb:
        cb(ret)
        del g_post_callback[sn]
    else:
        print "not exist post sn", sn


def test():
    print "testtestbanbang"
    t = Timer()
    t.SetTimer(3, foo)


def foo():
    pb = logic_pb2.L2CNotifyReadyStatus()
    pb.desc =  "Broadcast-bin"
    go.SendMsg(1, 2, 33, pb.SerializeToString(), server_pb2.Broadcast)
    pb.desc =  "Randomcast-bin"
    go.SendMsg(1, 2, 77, pb.SerializeToString(), server_pb2.Randomcast)
    t = Timer()
    t.SetTimer(3, foo)

