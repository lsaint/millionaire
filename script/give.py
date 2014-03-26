

import md5, json, time, logging
from post import PostAsync, GetPostSn
from config import *
from datetime import datetime

GIVE_URL = "http://113.106.100.103:28891/vm_add"

GIVED = {}


def give(uid, money=500):
    global GIVED
    y = datetime.now().timetuple().tm_yday
    if GIVED.get(y) is None:
        GIVED = {y:[]}
    lt = GIVED[y]
    if uid not in lt:
        _give(uid, money)
        lt.append(uid)


def _give(uid, money):
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
    def done(sn, ret):
        logging.debug("test-give uid:%d money:%d ret:%s" % (uid, money, ret))
    PostAsync(GIVE_URL, jn, done)

