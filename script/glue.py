# -*- coding: utf-8 -*-

import sys; sys.path.extend(["./conf/", "./proto/", "./script/"])
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
        print traceback.format_exc()


def OnTicker():
    try:
        Timer.Update()
    except Exception as err:
        print traceback.format_exc()


def OnPostDone(sn, ret):
    try:
        post.OnPostDone(sn, ret)
    except Exception as err:
        print traceback.format_exc()


def test():
    print "testtestbanbang"
    from award import AwardChecker
    achecker = AwardChecker(None, None)
    achecker.post2Vm([10593000], 37)
