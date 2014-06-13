# -*- coding: utf-8 -*-

import sys; sys.path.extend(["./conf/", "./proto/", "./script/"])
import logging
import traceback
import server_pb2, logic_pb2
import go
import post

from timer import Timer
from watchdog import watchdog
from config import *




def OnProto(tsid, ssid, uri, data, uid):
    #logging.debug("OnProto--> tsid:%s ssid:%s uri:%d len:%d" % (tsid, ssid, uri, len(data)))
    try:
        watchdog.Dispatch(tsid, ssid, uri, data, uid)
    except Exception as err:
        logging.error("%s-%s" % ("OnProto", traceback.format_exc()))


def OnTicker():
    try:
        Timer.Update()
    except Exception as err:
        logging.error("%s-%s" % ("OnTicker", traceback.format_exc()))


def OnPostDone(sn, ret):
    try:
        post.OnPostDone(sn, ret)
    except Exception as err:
        logging.error("%s-%s" % ("OnPostDone", traceback.format_exc()))



def OnHttpReq(jn, kind):
    print "python OnHttpReq", jn, kind
    return "glue\n"


def test():
    logging.debug("testtestbanbang")
