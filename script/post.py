# -*- coding: utf-8 -*-

import go

g_post_sn = 0
g_post_callback = {}


def GetPostSn():
    global g_post_sn
    g_post_sn += 1
    return g_post_sn


def OnPostDone(sn, ret):
    global g_post_callback
    cb = g_post_callback.get(sn)
    if cb:
        cb(sn, ret)
        del g_post_callback[sn]
    else:
        print "not exist post sn", sn


def PostAsync(url, s, func=None, sn=None):
    global g_post_callback
    go.PostAsync(url, s, sn or GetPostSn())
    if func:
        g_post_callback[sn] = func

