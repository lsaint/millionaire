# -*- coding: utf-8 -*-

import redigo, redis, cPickle
from config import *

redigo.dial(REDIGO_NETWORK, UNIX_DOMAIN_REDIS)

g_cache = redis.StrictRedis(unix_socket_path=UNIX_DOMAIN_REDIS, db=0)
g_cache.ping()


class CacheCenter(object):

    key_state = "mill:state"    # {(tsid, ssid): pickle_data}
    key_flag = "mill:flag"      # {(tsid, ssid): pickle_data}

    def __init__(self, tsid, ssid):
        self.tsid = tsid
        self.ssid = ssid
        self.prefix = "mill:%d:%d:" % (self.tsid, self.ssid)
        self.key_lpu = self.prefix + "logined.player.uids"
        self.key_rpu = self.prefix + "revived.player.uids"
        self.key_pu = self.prefix + "presenter.uid"
        self.key_pa = self.prefix + "player.answer"
        self.key_ca = self.prefix + "player.capture.actions"
        self.key_ft1 = self.prefix + "player.flag.top1"


    @classmethod
    def GetCacheState(cls):
        return g_cache.hgetall(cls.key_state)


    @classmethod
    def GetCacheFlag(cls):
        return g_cache.hgetall(cls.key_flag)

    #

    def CacheState(self, pickle_data):
        #g_cache.hset(self.key_state, (self.tsid, self.ssid), pickle_data)
        redigo.do("hset", self.key_state, str((self.tsid, self.ssid)), pickle_data)


    def CacheLoginedPlayer(self, uid, name):
        #g_cache.hset(self.key_lpu, uid, name)
        redigo.do("hset", self.key_lpu, str(uid), name)
        print("hset", self.key_lpu, str(uid), name)


    def CacheLogoutedPlayer(self, uid):
        #g_cache.hset(self.key_lpu, uid, "")
        redigo.do("hset", self.key_lpu, str(uid), "")


    def CacheRevivedPlayer(self, uid):
        #g_cache.lpush(self.key_rpu, uid)
        redigo.do("lpush", self.key_rpu, str(uid))


    def CachePresenter(self, uid):
        #g_cache.set(self.key_pu, uid)
        redigo.do("set", self.key_pu, str(uid))


    def CachePlayerAnswer(self, uid, answer):
        #g_cache.hset(self.key_pa, uid, answer)
        redigo.do("hset", self.key_pa, str(uid), str(answer))


    # flag
    def CacheFlagStatus(self, pickle_data):
        #g_cache.hset(self.key_flag, (self.tsid, self.ssid), pickle_data)
        redigo.do("hset", self.key_flag, str((self.tsid, self.ssid)), pickle_data)


    def CacheCaptureAction(self, pickle_action):
        #g_cache.lpush(self.key_ca, pickle_action)
        redigo.do("lpush", self.key_ca, pickle_action)


    def CacheFlagTop1(self, uid):
        #g_cache.set(self.key_ft1, uid)
        redigo.do("set", self.key_ft1, str(uid))


    # flag end

    def Clear(self):
        #g_cache.delete(self.key_lpu, self.key_rpu, self.key_pu, self.key_pa)
        redigo.do("delete", self.key_lpu, self.key_rpu, self.key_pu, self.key_pa)


    def ClearFlag(self):
        #g_cache.delete(self.key_ca, self.key_ft1)
        redigo.do("delete", self.key_ca, self.key_ft1)


    def GetLoginoutedPlayers(self):
        ret = g_cache.hgetall(self.key_lpu)
        r = {}
        for uid, name in ret.iteritems():
            r[int(uid)] = name
        return r


    def GetRevivedPlayers(self):
        ret = g_cache.lrange(self.key_rpu, 0, -1)
        return map(lambda x: int(x), ret)


    def GetPresenter(self):
        ret = g_cache.get(self.key_pu)
        if ret != None:
            ret = int(ret)
        return ret


    def GetPlayerAnswers(self):
        ret = g_cache.hgetall(self.key_pa)
        r = {}
        for k, v in ret.iteritems():
            r[int(k)] = int(v)
        return r


    def GetCaptureActions(self):
        ret = g_cache.lrange(self.key_ca, 0, -1)
        return map(lambda x: cPickle.loads(x), ret)


    def GetFlagTop1(self):
        ret = g_cache.get(self.key_ft1)
        if ret != None:
            return int(ret)
        return 0

