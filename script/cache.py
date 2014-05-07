# -*- coding: utf-8 -*-

import redis
from config import *

g_cache = redis.StrictRedis(host = HOST_REDIS, port = PORT_REDIS, db=0)
g_cache.ping()


class CacheCenter(object):

    key_state = "mill:state"    # {(tsid, ssid): pickle_data}

    def __init__(self, tsid, ssid):
        self.tsid = tsid
        self.ssid = ssid
        self.prefix = "mill:%d:%d:" % (self.tsid, self.ssid)
        self.key_lpu = self.prefix + "logined.player.uids"
        self.key_rpu = self.prefix + "revived.player.uids"
        self.key_pu = self.prefix + "presenter.uid"
        self.key_pa = self.prefix + "player.answer"


    @classmethod
    def GetCacheState(cls):
        return g_cache.hgetall(cls.key_state)


    def CacheState(self, pickle_data):
        g_cache.hset(self.key_state, (self.tsid, self.ssid), pickle_data)


    def CacheLoginedPlayer(self, uid, name):
        g_cache.lpush(self.key_lpu, (uid, name))


    def CacheRevivedPlayer(self, uid):
        g_cache.lpush(self.key_rpu, uid)


    def CachePresenter(self, uid):
        g_cache.set(self.key_pu, uid)


    def CachePlayerAnswer(self, uid, answer):
        g_cache.hset(self.key_pa, uid, answer)


    def Clear(self):
        g_cache.delete(self.key_lpu, self.key_rpu, self.key_pu, self.key_pa)


    def GetLoginedPlayers(self):
        ret = g_cache.lrange(self.key_lpu, 0, -1)
        return map(lambda x: eval(x), ret)


    def GetRevivedPlayers(self):
        ret = g_cache.lrange(self.key_rpu, 0, -1)
        return map(lambda x: int(x), ret)


    def GetPresenter(self):
        return int(g_cache.get(self.key_pu) or 0)


    def GetPlayerAnswers(self):
        ret = g_cache.hgetall(self.key_pa)
        for k, v in ret.iteritems():
            ret[int(k)] = int(v)
        return ret


