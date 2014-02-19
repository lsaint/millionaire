# -*- coding: utf-8 -*-

import go

g_post_sn = 1
g_post_callback = {}


def OnPostDone(sn, ret):
    global g_post_callback
    cb = g_post_callback.get(sn)
    if cb:
        cb(ret)
        del g_post_callback[sn]
    else:
        print "not exist post sn", sn


def PostAsync(url, s, func):
    global g_post_sn, g_post_callback
    sn = g_post_sn
    g_post_sn = g_post_sn + 1
    go.PostAsync(url, s, sn)
    if func:
        g_post_callback[sn] = func

