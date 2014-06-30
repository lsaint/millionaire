# -*- coding: utf-8 -*-

import json, logging, hmac, hashlib
from post import PostAsync
from config import *


def UpdateStatus(ssid, st):
    sign = hmac.new(BOX_KEY, "%d%d%d" % (BOX_APPID, st, ssid), hashlib.sha1).hexdigest()
    dt = {"appid": BOX_APPID, "status": st, "subsid": ssid, "sign": sign}
    def done(sn, ret):
        logging.debug("update box status %d, ret: %s" % (st, ret))
    PostAsync(BOX_URL_STATUS, json.dumps(dt), done)


def ListAll(rooms):
    sts = []
    for room in rooms:
        sts.append({"subsid": room.ssid, "status": int(room.IsStarted())})
    ret = {"ret": 1, "count": len(rooms), "statuses": sts}
    return json.dumps(ret)
