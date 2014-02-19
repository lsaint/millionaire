# -*- coding: utf-8 -*-
#


import go, json
from logic_pb2 import *
from timer import Timer

WARMUP_MATCH_ID = 1
LOAD_MATCH_INTERVAL = 60

class MatchMgr(object):

    def __init__(self):
        self.matchs = {}    # GameMatch
        self.timer = Timer()


    def startLoad(self):
        self.timer.SetTimer(LOAD_MATCH_INTERVAL, self.load, self)


    def load(self):
        jn = "[]"
        lt = json.loads(jn)
        for i, m in lt:
            self.matchs[m.id] = m


    def GetMatchList(self):
        ret = []
        for k, v in self.matchs.items():
            ret.append(v)
        return ret


    def GetWarmupMatch(self):
        return self.matchs.get(WARMUP_MATCH_ID)


    def GetMatch(self, mid):
        return self.matchs.get(mid)



g_match_mgr = MatchMgr()
g_match_mgr.startLoad()

