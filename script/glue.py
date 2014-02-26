# -*- coding: utf-8 -*-

import sys; sys.path.extend(["./proto/", "./script/"])
import traceback
import server_pb2, logic_pb2
import go
import post

from timer import Timer
from watchdog import watchdog



def OnProto(tsid, ssid, uri, data):
    print "python OnProto:", tsid, ssid, uri, len(data)
    try:
        watchdog.dispatch(tsid, ssid, uri, data)
    except Exception as err:
        print "--------err----------"
        print traceback.format_exc()


def OnTicker():
    Timer.Update()


def OnPostDone(sn, ret):
    post.OnPostDone(sn, ret)


def test():
    print "testtestbanbang"
    from award import AwardChecker
    achecker = AwardChecker(None, None)
    achecker.post2Vm([10593000], 37)
