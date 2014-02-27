# -*- coding: utf-8 -*-
#


import go, json, time
from datetime import datetime

from logic_pb2 import *
from timer import Timer
from config import *


class MatchMgr(object):

    def __init__(self):
        self.preview = None
        self.matchs = {}    # GameMatch
        self.timer = Timer()
        self.valid_presenters = []


    def startLoad(self):
        self.load()
        self.timer.SetTimer(LOAD_MATCH_INTERVAL, self.load)


    def load(self):
        from jn import jn_match     #test
        lt = json.loads(jn_match)
        for m in lt:
            self.matchs[m["id"]] = self.loadMatch(m)
        print "load match sucess.."
        self.loadPreview()


    def loadPresenterWhiteList(self):
        from jn import jn_presenter_wl
        self.valid_presenters = json.loads(jn_presenter_wl)
        print "load presenter whitelist sucess.."


    def loadPreview(self):
        from jn import jn_preview
        pv = json.loads(jn_preview)
        start_s = time.strptime(pv["start"], TIME_FORMAT)
        end_s = time.strptime(pv["end"], TIME_FORMAT)
        start = datetime.fromtimestamp(time.mktime(start_s))
        end = datetime.fromtimestamp(time.mktime(end_s))
        now = datetime.now()
        if start < now and now < end:
            pb = L2CNotifyPreview()
            pb.desc = pv["desc"]
            pb.start = pv["start"]
            pb.end = pv["end"]
            self.preview = pb
        print "load preview sucess.."


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


    def GetPreview(self):
        return self.preview


    def IsValidPresenter(self, uid):
        return uid in self.valid_presenters


g_match_mgr = MatchMgr()
g_match_mgr.startLoad()

