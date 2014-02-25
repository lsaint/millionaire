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
        self.load()
        self.timer.SetTimer(LOAD_MATCH_INTERVAL, self.load)


    def load(self):
        from jn import jn_match     #test
        lt = json.loads(jn_match)
        for m in lt:
            self.matchs[m["id"]] = self.loadMatch(m)
        print "load match sucess.."


    def loadMatch(self, m):
        #print "m", m
        match = GameMatch()
        match.id = m["id"]
        match.name = m["name"]
        match.pid = m["pid"]

        m_ra = m["race_award"]
        if m_ra:
            ra = match.race_award
            ra.refuse_revive_id = m_ra["refuse_revive_id"]
            ra.final_id = m_ra["final_id"]

            sections = m_ra["sections"]
            for section in sections:
                ras = match.race_award.sections.add()
                ras.id = section["id"]
                ras.trigger_id = section["trigger_id"]
                ras.survivor_num = section["survivor_num"]
                ras.bounty = section["bounty"]

        m_pa = m["personal_award"]
        if m_pa:
            pa = match.personal_award
            pa.start_id = m_pa["start_id"]
            pa.end_id = m_pa["end_id"]
            pa.bingo_time = m_pa["bingo_time"]
            pa.bounty = m_pa["bounty"]

        return match



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

