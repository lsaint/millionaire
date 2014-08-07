

import md5, json, time, log
from post import PostAsync, GetPostSn
from config import *
from local import *
from datetime import datetime

GIVE_URL = VM_HEAD + "/vm_add"

GIVED = {}


def give(uid, cb, money=TEST_GIVE_SILVER):
    global GIVED
    y = datetime.now().timetuple().tm_yday
    if GIVED.get(y) is None:
        GIVED = {y:[]}
    lt = GIVED[y]
    if uid not in lt:
        _give(uid, cb, money)
        lt.append(uid)


def _give(uid, cb, money):
    product = VM_PRODUCT
    money_type = 2
    orderid = "%s%s" % (str(time.time()), str(GetPostSn()))
    add_time = time.strftime("%Y%m%d%H%M%S")
    desc = "test-give"
    sign = md5.new("%d%s%d%d%d%s%s%s%s" % (uid, orderid, money, money_type, VM_APPID,
                            product, add_time, desc, VM_KEY)).hexdigest()
    dt = {"product": product,
          "uid": uid,
          "appid": VM_APPID,
          "money": money,
          "money_type": money_type,
          "orderid": orderid,
          "add_time": add_time,
          "desc": desc,
          "sign": sign}
    jn = json.dumps(dt)
    PostAsync(GIVE_URL, jn, cb)

